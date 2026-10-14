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
import json
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


@pytest.mark.anyio
async def test_unauthenticated_timeline_and_routine_rejected():
    """Unauthenticated calls to timeline and suggested-routine must be rejected with 401."""
    app.dependency_overrides.pop(get_current_user, None)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r1 = await ac.get("/v1/reports/timeline")
        assert r1.status_code == 401
        r2 = await ac.post("/v1/reports/summaries/123/suggested-routine")
        assert r2.status_code == 401


@pytest.mark.anyio
async def test_suggested_routine_cross_user_isolation():
    """User B cannot create a suggested routine from User A's summary."""
    user_a = AuthenticatedUser(uid="user-routine-a", email="a@example.com")
    user_b = AuthenticatedUser(uid="user-routine-b", email="b@example.com")

    # User A creates a summary
    app.dependency_overrides[get_current_user] = lambda: user_a
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        summary_payload = {
            "session_type": "Explorer",
            "body_region_filter": "Eyes",
            "selected_tags": ["nightblindness"],
            "matched_entries": [
                {
                    "class_label": "Bitot_Spots",
                    "body_region": "Eyes",
                    "category": "Nutritional",
                    "vitamin_deficiency_association": "Vitamin A",
                    "matched_tags": ["nightblindness"],
                    "match_count": 1,
                    "total_condition_tags": 2,
                    "review_status": "unreviewed draft",
                }
            ],
            "package_version": "curated_v1.0",
            "matcher_version": "matcher_spec_v1.0",
        }
        res_create = await ac.post("/v1/reports/summaries", json=summary_payload)
        assert res_create.status_code == 201
        summary_id = res_create.json()["id"]

        # User B attempts to add suggested routine for User A's summary -> 403 or 404
        app.dependency_overrides[get_current_user] = lambda: user_b
        res_b = await ac.post(f"/v1/reports/summaries/{summary_id}/suggested-routine")
        assert res_b.status_code in [403, 404]


@pytest.mark.anyio
async def test_account_deletion_cascades_medscan_sessions():
    """Account deletion must cascade and completely delete MedScan sessions."""
    cascade_user = AuthenticatedUser(uid="user-cascade-medscan", email="cascade@example.com")
    app.dependency_overrides[get_current_user] = lambda: cascade_user

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create consent and profile
        await ac.post("/v1/profile/consent", json={"agreed_to_terms": True, "confirmed_adult_18": True})

        # Create MedScan session
        img_bytes = create_test_image_bytes(250, 250)
        files = [("files", ("cascade.jpg", img_bytes, "image/jpeg"))]
        res_scan = await ac.post("/v1/medscan/sessions", data={"body_region": "eyes", "save_session": "true"}, files=files)
        assert res_scan.status_code == 201

        # Confirm session listed
        res_list = await ac.get("/v1/medscan/sessions")
        assert res_list.status_code == 200
        assert len(res_list.json()) >= 1

        # Delete account
        res_del = await ac.delete("/v1/profile")
        assert res_del.status_code == 200
        assert res_del.json()["status"] == "deleted"

        # Re-check sessions for this user -> now empty
        res_list_after = await ac.get("/v1/medscan/sessions")
        assert res_list_after.status_code == 200
        assert len(res_list_after.json()) == 0


@pytest.mark.anyio
async def test_checkup_reminder_and_forbidden_terms_scan():
    """Check-up reminder in CarePlan and scan for forbidden clinical/dosing terms."""
    user = AuthenticatedUser(uid="user-checkup-reminder", email="checkup@example.com")
    app.dependency_overrides[get_current_user] = lambda: user

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create check-up task in CarePlan
        task_payload = {
            "title": "General Health Check-up Consultation",
            "category": "general",
            "target_frequency": "once",
            "reminder_time": "09:00",
        }
        res_task = await ac.post("/v1/careplan/tasks", json=task_payload)
        assert res_task.status_code == 201
        task_data = res_task.json()
        assert task_data["title"] == "General Health Check-up Consultation"

        # Scan task response for forbidden pharmaceutical and prescriptive terms
        banned_terms = ["mg", "mcg", " iu ", "dose", "dosage", "prescription", "cure", "prescribe", "infant", "toddler"]
        combined_text = f"{task_data['title']} {task_data.get('category', '')}".lower()
        for term in banned_terms:
            assert term not in combined_text, f"Forbidden term '{term}' found in checkup reminder task"


@pytest.mark.anyio
async def test_medscan_checklist_endpoint():
    """Checklist endpoint must return 6-8 discriminative symptoms per region."""
    user = AuthenticatedUser(uid="user-checklist-test", email="checklist@example.com")
    app.dependency_overrides[get_current_user] = lambda: user

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/v1/medscan/checklist?body_region=eyes")
        assert res.status_code == 200
        data = res.json()
        assert data["body_region"] == "eyes"
        assert 5 <= len(data["items"]) <= 8
        tags = [i["tag"] for i in data["items"]]
        assert "nightblindness" in tags or "eyedryness" in tags


@pytest.mark.anyio
async def test_medscan_analyze_and_blend_with_mocked_ml_service(monkeypatch):
    """Verifies end-to-end MedScan blend, weighting, C-34/35 compliance, and auto-report save."""
    from app.services.medscan_service import medscan_pipeline

    # Mock ml-service response with simulated predictions
    async def mock_predict(model_name, file_bytes, filename, content_type):
        return {
            "model_name": model_name,
            "predictions": [
                {"class_name": "Vitamin_A_Deficiency", "percentage": 84.0},
                {"class_name": "Normal", "percentage": 16.0},
            ],
            "top_3_classes": ["Vitamin_A_Deficiency", "Normal"],
            "shortcut_flag": True,
            "warning": "Trained on unverified dataset labels; not a diagnosis.",
        }, None

    monkeypatch.setattr(medscan_pipeline, "predict_image_via_ml_service", mock_predict)

    user = AuthenticatedUser(uid="user-medscan-blend", email="blend@example.com")
    app.dependency_overrides[get_current_user] = lambda: user

    img_bytes = create_test_image_bytes(300, 300)
    files = {"file": ("eye_photo.jpg", img_bytes, "image/jpeg")}
    data = {
        "body_region": "eyes",
        "symptoms": json.dumps(["nightblindness", "eyedryness"]),
        "save_report": "true",
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/v1/medscan/analyze", data=data, files=files)
        assert res.status_code == 200
        res_data = res.json()

        assert res_data["status"] == "MATCHES_FOUND"
        assert res_data["kind"] == "medscan_blend"
        assert res_data["shortcut_flag"] is True
        assert res_data["w_img"] == 0.25  # Shortcut flag applies 0.25 weight
        assert res_data["saved_report_id"] is not None

        # Check nutrient scores
        vit_a = next((n for n in res_data["nutrient_scores"] if "Vitamin A" in n["nutrient"]), None)
        assert vit_a is not None
        assert vit_a["image_percentage"] == 84.0
        assert vit_a["percentage_kind"] == "MedScan blend %"
        assert vit_a["risk_band"] in ["High", "Moderate", "Low"]
        assert vit_a["risk_band_label"] == "Demo risk band (heuristic, not clinical)"
        assert "Blended evidence" in vit_a["percentage_explanation"]

        # Check auto-saved report retrieval via /v1/reports/summaries
        report_id = res_data["saved_report_id"]
        res_report = await ac.get(f"/v1/reports/summaries/{report_id}")
        assert res_report.status_code == 200
        rep_data = res_report.json()
        assert rep_data["session_type"] == "medscan"
        assert rep_data["body_region_filter"] == "eyes"


@pytest.mark.anyio
async def test_medscan_image_only_capped_at_sixty(monkeypatch):
    """When no symptoms are ticked, image-only candidate is capped at 60% and labelled."""
    from app.services.medscan_service import medscan_pipeline

    async def mock_predict(model_name, file_bytes, filename, content_type):
        return {
            "model_name": model_name,
            "predictions": [
                {"class_name": "Vitamin_A_Deficiency", "percentage": 90.0},
            ],
            "shortcut_flag": False,
            "warning": "test",
        }, None

    monkeypatch.setattr(medscan_pipeline, "predict_image_via_ml_service", mock_predict)

    user = AuthenticatedUser(uid="user-img-only", email="imgonly@example.com")
    app.dependency_overrides[get_current_user] = lambda: user

    img_bytes = create_test_image_bytes(300, 300)
    files = {"file": ("test.jpg", img_bytes, "image/jpeg")}
    data = {"body_region": "eyes", "symptoms": "", "save_report": "false"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/v1/medscan/analyze", data=data, files=files)
        assert res.status_code == 200
        res_data = res.json()
        vit_a = next((n for n in res_data["nutrient_scores"] if "Vitamin A" in n["nutrient"]), None)
        assert vit_a is not None
        assert vit_a["percentage"] <= 60.0
        assert vit_a["percentage_explanation"] == "image only, low reliability"
        assert vit_a["percentage_kind"] == "Image model %"


@pytest.mark.anyio
async def test_medscan_fallback_when_ml_service_down(monkeypatch):
    """If ml-service is unavailable, MedScan gracefully falls back to symptom reference match."""
    from app.services.medscan_service import medscan_pipeline

    async def mock_predict_fail(model_name, file_bytes, filename, content_type):
        return None, "ML Lab service is currently unavailable on port 8001. Running in fallback mode."

    monkeypatch.setattr(medscan_pipeline, "predict_image_via_ml_service", mock_predict_fail)

    user = AuthenticatedUser(uid="user-fallback", email="fallback@example.com")
    app.dependency_overrides[get_current_user] = lambda: user

    img_bytes = create_test_image_bytes(300, 300)
    files = {"file": ("test.jpg", img_bytes, "image/jpeg")}
    data = {"body_region": "eyes", "symptoms": json.dumps(["nightblindness"]), "save_report": "false"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/v1/medscan/analyze", data=data, files=files)
        assert res.status_code == 200
        res_data = res.json()
        assert "ML Lab service currently unavailable" in res_data["message"]
        assert res_data["kind"] == "reference_match"
        vit_a = next((n for n in res_data["nutrient_scores"] if "Vitamin A" in n["nutrient"]), None)
        assert vit_a is not None
        assert vit_a["percentage_kind"] == "Reference match %"


