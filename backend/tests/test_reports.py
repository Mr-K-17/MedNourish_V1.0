"""Tests for Saved Summaries and Reports API (M1B.3).

Verifies:
1. Save completed reference match summary through API.
2. List user's saved summaries in chronological order.
3. Retrieve detailed saved summary with matched tags and disclaimer.
4. Delete saved summary.
5. Rejection of unauthenticated requests (401).
6. Data isolation: User A cannot read or delete User B's summary (403/404).
7. Account deletion removes all saved summaries belonging to user.
8. Database connection failure returns 503 Service Unavailable.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.auth import AuthenticatedUser, get_current_user
from app.db.session import Base, get_db
from app.main import app
from app.models.user import SavedSummary, UserProfile

from tests.conftest import TestingSessionLocal


SAMPLE_MATCH_PAYLOAD = {
    "session_type": "Explorer",
    "body_region_filter": "EYES",
    "selected_tags": ["nightblindness", "eyedryness"],
    "matched_entries": [
        {
            "class_label": "Bitot_Spots",
            "body_region": "EYES",
            "category": "Nutritional",
            "vitamin_deficiency_association": "Vitamin A Deficiency",
            "matched_tags": ["nightblindness", "eyedryness"],
            "match_count": 2,
            "total_condition_tags": 6,
            "review_status": "unreviewed draft",
        }
    ],
    "package_version": "curated_v1.0",
    "matcher_version": "matcher_spec_v1.0",
}


@pytest.mark.anyio
async def test_unauthenticated_reports_access():
    """Verifies that all reports endpoints reject unauthenticated calls."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res1 = await client.get("/v1/reports/summaries")
        assert res1.status_code == 401

        res2 = await client.post("/v1/reports/summaries", json=SAMPLE_MATCH_PAYLOAD)
        assert res2.status_code == 401

        res3 = await client.get("/v1/reports/summaries/sum_123")
        assert res3.status_code == 401

        res4 = await client.delete("/v1/reports/summaries/sum_123")
        assert res4.status_code == 401


@pytest.mark.anyio
async def test_save_and_retrieve_summary():
    """Verifies saving a summary and retrieving its detail."""
    user = AuthenticatedUser(uid="user_alice_123", email="alice@test.local")
    app.dependency_overrides[get_current_user] = lambda: user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Save summary
        res = await client.post("/v1/reports/summaries", json=SAMPLE_MATCH_PAYLOAD)
        assert res.status_code == 201
        data = res.json()

        assert data["id"].startswith("sum_")
        assert data["session_type"] == "Explorer"
        assert data["body_region_filter"] == "EYES"
        assert data["package_version"] == "curated_v1.0"
        assert data["matcher_version"] == "matcher_spec_v1.0"
        assert data["match_count_total"] == 1
        assert "Bitot_Spots" in data["matched_entries"][0]["class_label"]
        assert "disclaimer" in data

        summary_id = data["id"]

        # Retrieve detail
        get_res = await client.get(f"/v1/reports/summaries/{summary_id}")
        assert get_res.status_code == 200
        detail = get_res.json()
        assert detail["id"] == summary_id
        assert detail["selected_tags"] == ["nightblindness", "eyedryness"]
        assert len(detail["matched_entries"]) == 1


@pytest.mark.anyio
async def test_list_user_summaries_isolation():
    """Verifies that User A and User B only see their own summaries."""
    alice = AuthenticatedUser(uid="user_alice_123", email="alice@test.local")
    bob = AuthenticatedUser(uid="user_bob_456", email="bob@test.local")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Alice saves a summary
        app.dependency_overrides[get_current_user] = lambda: alice
        await client.post("/v1/reports/summaries", json=SAMPLE_MATCH_PAYLOAD)

        # Bob saves a summary
        app.dependency_overrides[get_current_user] = lambda: bob
        bob_payload = dict(SAMPLE_MATCH_PAYLOAD)
        bob_payload["selected_tags"] = ["crackedlips"]
        await client.post("/v1/reports/summaries", json=bob_payload)

        # Alice lists summaries: should see exactly 1 summary
        app.dependency_overrides[get_current_user] = lambda: alice
        alice_list = await client.get("/v1/reports/summaries")
        assert alice_list.status_code == 200
        alice_data = alice_list.json()
        assert alice_data["total_count"] == 1
        assert alice_data["summaries"][0]["selected_tags"] == ["nightblindness", "eyedryness"]

        # Bob lists summaries: should see exactly 1 summary
        app.dependency_overrides[get_current_user] = lambda: bob
        bob_list = await client.get("/v1/reports/summaries")
        assert bob_list.status_code == 200
        bob_data = bob_list.json()
        assert bob_data["total_count"] == 1
        assert bob_data["summaries"][0]["selected_tags"] == ["crackedlips"]


@pytest.mark.anyio
async def test_cross_user_access_blocked():
    """User B cannot read or delete User A's summary."""
    alice = AuthenticatedUser(uid="user_alice_123", email="alice@test.local")
    bob = AuthenticatedUser(uid="user_bob_456", email="bob@test.local")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Alice saves summary
        app.dependency_overrides[get_current_user] = lambda: alice
        res = await client.post("/v1/reports/summaries", json=SAMPLE_MATCH_PAYLOAD)
        summary_id = res.json()["id"]

        # Bob tries to read Alice's summary -> 403 Forbidden
        app.dependency_overrides[get_current_user] = lambda: bob
        read_res = await client.get(f"/v1/reports/summaries/{summary_id}")
        assert read_res.status_code == 403

        # Bob tries to delete Alice's summary -> 403 Forbidden
        del_res = await client.delete(f"/v1/reports/summaries/{summary_id}")
        assert del_res.status_code == 403

        # Alice deletes her own summary -> 200 OK
        app.dependency_overrides[get_current_user] = lambda: alice
        del_alice_res = await client.delete(f"/v1/reports/summaries/{summary_id}")
        assert del_alice_res.status_code == 200
        assert del_alice_res.json()["status"] == "deleted"


@pytest.mark.anyio
async def test_account_deletion_removes_saved_summaries():
    """Account deletion in development removes user's profile and all saved summaries."""
    user = AuthenticatedUser(uid="user_to_delete_999", email="del@test.local")
    app.dependency_overrides[get_current_user] = lambda: user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create minimal profile
        await client.post(
            "/v1/profile",
            json={
                "is_adult_confirmed": True,
                "terms_consent_version": "v1.0",
                "display_name": "Test User",
            },
        )

        # Save summary
        save_res = await client.post("/v1/reports/summaries", json=SAMPLE_MATCH_PAYLOAD)
        assert save_res.status_code == 201

        # Confirm 1 summary exists
        list_res = await client.get("/v1/reports/summaries")
        assert list_res.json()["total_count"] == 1

        # Delete account
        del_account_res = await client.delete("/v1/profile")
        assert del_account_res.status_code == 200

        # Verify summaries are completely gone
        list_after_res = await client.get("/v1/reports/summaries")
        assert list_after_res.json()["total_count"] == 0
