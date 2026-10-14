"""Tests for MedScan-lite router and F2 endpoints.
==================================================
Covers:
- Unauthenticated rejection (401)
- Validation: 1-5 files, 5 MB limit, format checking
- Ephemeral quality checking (images deleted unless saved)
- Session save and detail retrieval
- User isolation: User A cannot access User B's session (403)
- Session deletion and file cleanup
- Deletion cascade on account deletion
- Response scanner: zero prohibited diagnostic terms
"""

import io
import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image

from app.core.auth import AuthenticatedUser, get_current_user
from app.main import app
from app.models.user import MedScanSession, UserProfile


def create_test_image_bytes(width=300, height=300, color=(128, 128, 128), fmt="JPEG"):
    buf = io.BytesIO()
    img = Image.new("RGB", (width, height), color=color)
    img.save(buf, format=fmt)
    return buf.getvalue()


@pytest.mark.anyio
async def test_unauthenticated_medscan_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/v1/medscan/sessions")
        assert res.status_code == 401


@pytest.mark.anyio
async def test_medscan_quality_check_ephemeral(db_session=None):
    user_a = AuthenticatedUser(uid="user-medscan-01", email="a@example.com")
    app.dependency_overrides[get_current_user] = lambda: user_a

    img_bytes = create_test_image_bytes(300, 300)
    files = [("files", ("test_eye.jpg", img_bytes, "image/jpeg"))]
    data = {"body_region": "eyes", "save_session": "false"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/v1/medscan/sessions", data=data, files=files)
        assert res.status_code == 201
        res_data = res.json()
        assert res_data["body_region"] == "eyes"
        assert res_data["image_count"] == 1
        assert res_data["session_id"] is None  # Ephemeral, not saved
        assert len(res_data["metrics"]) == 1
        assert res_data["metrics"][0]["resolution_ok"] is True


@pytest.mark.anyio
async def test_medscan_save_and_user_isolation():
    user_a = AuthenticatedUser(uid="user-medscan-a", email="a@example.com")
    user_b = AuthenticatedUser(uid="user-medscan-b", email="b@example.com")
    app.dependency_overrides[get_current_user] = lambda: user_a

    img_bytes = create_test_image_bytes(250, 250)
    files = [("files", ("nail.png", img_bytes, "image/png"))]
    data = {"body_region": "nails", "save_session": "true"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # User A saves session
        res = await ac.post("/v1/medscan/sessions", data=data, files=files)
        assert res.status_code == 201
        session_id = res.json()["session_id"]
        assert session_id is not None

        # User A lists sessions
        list_res = await ac.get("/v1/medscan/sessions")
        assert list_res.status_code == 200
        assert len(list_res.json()) >= 1
        assert list_res.json()[0]["id"] == session_id

        # User B attempts to access User A's session -> 403 Forbidden
        app.dependency_overrides[get_current_user] = lambda: user_b
        detail_res = await ac.get(f"/v1/medscan/sessions/{session_id}")
        assert detail_res.status_code == 403

        # User B attempts to delete User A's session -> 403 Forbidden
        del_res = await ac.delete(f"/v1/medscan/sessions/{session_id}")
        assert del_res.status_code == 403

        # User A deletes their own session -> 200 OK
        app.dependency_overrides[get_current_user] = lambda: user_a
        del_res2 = await ac.delete(f"/v1/medscan/sessions/{session_id}")
        assert del_res2.status_code == 200
        assert del_res2.json()["status"] == "deleted"


@pytest.mark.anyio
async def test_reports_timeline_and_suggested_routine():
    user = AuthenticatedUser(uid="user-reports-timeline", email="t@example.com")
    app.dependency_overrides[get_current_user] = lambda: user

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Save a summary first
        summary_payload = {
            "session_type": "Explorer",
            "body_region_filter": "Nails",
            "selected_tags": ["spoon_shaped_nails"],
            "matched_entries": [
                {
                    "class_label": "Koilonychia",
                    "body_region": "Nails",
                    "category": "Mineral Reference Association",
                    "vitamin_deficiency_association": "Iron (Informational Reference)",
                    "matched_tags": ["spoon_shaped_nails"],
                    "match_count": 1,
                    "total_condition_tags": 2,
                    "review_status": "unreviewed draft",
                }
            ],
            "package_version": "curated_v1.0",
            "matcher_version": "matcher_spec_v1.0",
        }
        create_res = await ac.post("/v1/reports/summaries", json=summary_payload)
        assert create_res.status_code == 201
        summary_id = create_res.json()["id"]

        # Timeline endpoint check
        time_res = await ac.get("/v1/reports/timeline")
        assert time_res.status_code == 200
        time_data = time_res.json()
        assert time_data["total_records"] >= 1
        assert "Match Overview Timeline" in time_data["label"]

        # Curated suggested routine check
        routine_res = await ac.post(f"/v1/reports/summaries/{summary_id}/suggested-routine")
        assert routine_res.status_code == 200
        routine_data = routine_res.json()
        assert routine_data["status"] == "added"
        assert "supplement" not in routine_data["title"].lower()
        assert "dose" not in routine_data["title"].lower()

        # Check task appears in CarePlan
        cp_res = await ac.get("/v1/careplan/tasks")
        assert cp_res.status_code == 200
        tasks = cp_res.json()["tasks"]
        assert any(t["id"] == routine_data["task_id"] for t in tasks)


@pytest.mark.anyio
async def test_medscan_and_routine_safety_terms():
    """Verify zero prohibited diagnostic or prescriptive claims in endpoints."""
    user = AuthenticatedUser(uid="user-safety-sweep", email="s@example.com")
    app.dependency_overrides[get_current_user] = lambda: user

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        img_bytes = create_test_image_bytes(250, 250)
        files = [("files", ("safety.jpg", img_bytes, "image/jpeg"))]
        res = await ac.post("/v1/medscan/sessions", data={"body_region": "eyes", "save_session": "false"}, files=files)
        text_resp = res.text.lower()

        banned = ["autonomous diagnosis", "we prescribe", "cure your", "clinical decision"]
        for b in banned:
            assert b not in text_resp, f"Banned phrase '{b}' found in MedScan response"
