"""Tests for NurseBot Scripted App Help API (M1B.6).

Verifies:
1. Rejection of unauthenticated requests (401).
2. Menu retrieval listing all scripted topics and categories.
3. Detail retrieval for valid topic IDs (including procedural app help).
4. Safety refusal retrieval for diagnosis, medication/dosage, and emergency inquiries (NURSE-03, NURSE-04, SAF-14).
5. 404 handling for unknown topic IDs.
6. Absence of transcripts or stored logs written to database during help interactions (NURSE-01, SAF-14).
7. Scanning scripted responses to verify zero unauthorized clinical assertions (prescriptions, diagnostic certainty).
"""

import pytest
from httpx import ASGITransport, AsyncClient
from app.core.auth import AuthenticatedUser, get_current_user
from app.db.session import get_db
from app.main import app
from app.models.user import CarePlanItem, SavedSummary, UserConsentLog, UserProfile
from tests.conftest import TestingSessionLocal


@pytest.mark.anyio
async def test_unauthenticated_nursebot_access():
    """All NurseBot endpoints require an authenticated user session."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # GET /v1/nursebot/menu
        res1 = await client.get("/v1/nursebot/menu")
        assert res1.status_code == 401

        # GET /v1/nursebot/topics/{id}
        res2 = await client.get("/v1/nursebot/topics/faq_how_medbot_works")
        assert res2.status_code == 401


@pytest.mark.anyio
async def test_nursebot_menu_structure():
    """Verifies that the menu response contains expected categories and scripted topics."""
    user = AuthenticatedUser(uid="user_help_tester", email="help@test.local")
    app.dependency_overrides[get_current_user] = lambda: user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/v1/nursebot/menu")
        assert res.status_code == 200
        data = res.json()

        assert "categories" in data
        assert "app_usage" in data["categories"]
        assert "safety_refusals" in data["categories"]
        assert len(data["topics"]) >= 5
        assert "disclaimer" in data
        assert "not a real nurse" in data["disclaimer"].lower()


@pytest.mark.anyio
async def test_scripted_safety_refusals():
    """Verifies specific scripted refusal patterns for diagnosis, medication, and emergencies (SAF-14)."""
    user = AuthenticatedUser(uid="user_help_tester", email="help@test.local")
    app.dependency_overrides[get_current_user] = lambda: user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Refusal on diagnosis request
        res_diag = await client.get("/v1/nursebot/topics/refusal_diagnosis")
        assert res_diag.status_code == 200
        diag_data = res_diag.json()
        assert diag_data["is_safety_refusal"] is True
        assert "cannot diagnose" in diag_data["content"].lower()
        assert "licensed physician" in diag_data["content"].lower()

        # 2. Refusal on medicine / dose request
        res_med = await client.get("/v1/nursebot/topics/refusal_medication_dose")
        assert res_med.status_code == 200
        med_data = res_med.json()
        assert med_data["is_safety_refusal"] is True
        assert "cannot advise on medicines" in med_data["content"].lower()
        assert "licensed pharmacist" in med_data["content"].lower()

        # 3. Emergency redirection
        res_urg = await client.get("/v1/nursebot/topics/refusal_emergency_urgent")
        assert res_urg.status_code == 200
        urg_data = res_urg.json()
        assert urg_data["is_safety_refusal"] is True
        assert "emergency services" in urg_data["content"].lower()


@pytest.mark.anyio
async def test_unknown_topic_not_found():
    """Requesting an unmapped topic returns 404."""
    user = AuthenticatedUser(uid="user_help_tester", email="help@test.local")
    app.dependency_overrides[get_current_user] = lambda: user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/v1/nursebot/topics/unknown_topic_xyz")
        assert res.status_code == 404
        assert "not found" in res.json()["detail"].lower()


@pytest.mark.anyio
async def test_no_chat_transcripts_written():
    """NurseBot is read-only; verifies zero database records or transcripts are written (NURSE-01, SAF-14)."""
    user = AuthenticatedUser(uid="user_help_tester", email="help@test.local")
    app.dependency_overrides[get_current_user] = lambda: user

    db = TestingSessionLocal()
    initial_profiles = db.query(UserProfile).count()
    initial_summaries = db.query(SavedSummary).count()
    initial_tasks = db.query(CarePlanItem).count()
    initial_consents = db.query(UserConsentLog).count()
    db.close()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Access menu and multiple topics
        await client.get("/v1/nursebot/menu")
        await client.get("/v1/nursebot/topics/faq_how_medbot_works")
        await client.get("/v1/nursebot/topics/refusal_medication_dose")

    db2 = TestingSessionLocal()
    assert db2.query(UserProfile).count() == initial_profiles
    assert db2.query(SavedSummary).count() == initial_summaries
    assert db2.query(CarePlanItem).count() == initial_tasks
    assert db2.query(UserConsentLog).count() == initial_consents
    db2.close()


@pytest.mark.anyio
async def test_prohibited_terms_scan_in_nursebot_content():
    """Scripted topics must never contain diagnostic certainty or treatment prescriptions."""
    user = AuthenticatedUser(uid="user_help_tester", email="help@test.local")
    app.dependency_overrides[get_current_user] = lambda: user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        menu_res = await client.get("/v1/nursebot/menu")
        topics = menu_res.json()["topics"]

        for t in topics:
            res = await client.get(f"/v1/nursebot/topics/{t['id']}")
            assert res.status_code == 200
            content = res.json()["content"].lower()

            # Prohibited phrases (unless explicitly stated as a negative refusal)
            assert "you have a deficiency" not in content
            assert "take this medication" not in content
            assert "guaranteed cure" not in content
