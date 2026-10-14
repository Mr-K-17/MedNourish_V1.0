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


@pytest.mark.anyio
async def test_nursebot_ask_unauthenticated():
    """POST /v1/nursebot/ask requires an authenticated user session (401)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/v1/nursebot/ask", json={"question": "What is vitamin C?"})
        assert res.status_code == 401


@pytest.mark.anyio
async def test_nursebot_ask_emergency_priority():
    """Emergency intent takes absolute priority over other keywords."""
    user = AuthenticatedUser(uid="user_emerg_tester", email="emerg@test.local")
    app.dependency_overrides[get_current_user] = lambda: user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Emergency combined with vitamin / dosage keywords
        res = await client.post(
            "/v1/nursebot/ask",
            json={"question": "I have severe chest pain and trouble breathing, what vitamin should I take?"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["intent"] == "emergency"
        assert "EMERGENCY ALERT" in data["reply"]
        assert "911" in data["reply"]
        assert data["is_web_answer"] is False


@pytest.mark.anyio
async def test_nursebot_ask_diagnosis_dosage_refusal():
    """Diagnosis and dosage inquiries trigger scripted refusal."""
    user = AuthenticatedUser(uid="user_refusal_tester", email="refusal@test.local")
    app.dependency_overrides[get_current_user] = lambda: user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Diagnosis
        res1 = await client.post(
            "/v1/nursebot/ask",
            json={"question": "Can you diagnose me? What illness do I have?"},
        )
        assert res1.status_code == 200
        data1 = res1.json()
        assert data1["intent"] == "refusal"
        assert "does not provide medical diagnoses or dosages" in data1["reply"]

        # 2. Dosage
        res2 = await client.post(
            "/v1/nursebot/ask",
            json={"question": "What dosage of zinc should I take?"},
        )
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["intent"] == "refusal"
        assert "does not provide medical diagnoses or dosages" in data2["reply"]


@pytest.mark.anyio
async def test_nursebot_ask_app_help():
    """App questions match against scripted help topics."""
    user = AuthenticatedUser(uid="user_apphelp_tester", email="apphelp@test.local")
    app.dependency_overrides[get_current_user] = lambda: user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/v1/nursebot/ask",
            json={"question": "How does MedBot symptom check questionnaire work?"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["intent"] == "app_help"
        assert "deterministic rule engine" in data["reply"]
        assert data["is_web_answer"] is False


@pytest.mark.anyio
async def test_nursebot_ask_web_reference_and_allowlist(monkeypatch):
    """Nutrition queries trigger web answer service with strict allowlist and <= 600 char truncation."""
    from app.services.web_answer_service import web_answer_service

    # Test allowlist
    assert web_answer_service._is_url_allowed("https://wsearch.nlm.nih.gov/ws/query?db=healthTopics") is True
    assert web_answer_service._is_url_allowed("https://medlineplus.gov/ency/article/002400.htm") is True
    assert web_answer_service._is_url_allowed("https://ods.od.nih.gov/factsheets/Zinc-HealthProfessional/") is True
    assert web_answer_service._is_url_allowed("https://unapproved-site.com/health") is False

    # Mock web request with a long XML response to test truncation <= 600 chars
    long_text = "Vitamin C, also known as ascorbic acid, is a water-soluble nutrient found in some foods. " * 15
    mock_xml = f"""
    <nlmSearchResult>
      <list>
        <document url="https://medlineplus.gov/vitaminc.html">
          <content name="title">Vitamin C</content>
          <content name="FullSummary">{long_text}</content>
        </document>
      </list>
    </nlmSearchResult>
    """

    class MockResponse:
        status_code = 200
        text = mock_xml

    async def mock_get(self, url, **kwargs):
        return MockResponse()

    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)

    user = AuthenticatedUser(uid="user_web_tester", email="web@test.local")
    app.dependency_overrides[get_current_user] = lambda: user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/v1/nursebot/ask",
            json={"question": "Tell me about vitamin C benefits and foods"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["intent"] == "web_reference"
        assert data["is_web_answer"] is True
        assert "MedlinePlus" in data["source_name"]
        assert data["source_url"] == "https://medlineplus.gov/vitaminc.html"
        assert len(data["reply"]) <= 600
        assert data["reply"].endswith("...")


@pytest.mark.anyio
async def test_nursebot_web_fallback_when_offline(monkeypatch):
    """Graceful fallback message when medical reference service is unreachable."""
    async def mock_fail_get(self, url, **kwargs):
        raise ConnectionError("Network unreachable")

    monkeypatch.setattr("httpx.AsyncClient.get", mock_fail_get)

    user = AuthenticatedUser(uid="user_offline_tester", email="offline@test.local")
    app.dependency_overrides[get_current_user] = lambda: user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/v1/nursebot/ask",
            json={"question": "What foods have zinc and iron?"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["intent"] == "web_reference"
        assert "Could not reach medical reference services" in data["reply"]
        assert data["is_web_answer"] is False


@pytest.mark.anyio
async def test_nursebot_rate_limiting():
    """Rate limit enforces max 10 queries per minute per user."""
    from app.services.nursebot_service import nursebot_service
    user_uid = "rate_limit_user_123"
    nursebot_service._rate_limits[user_uid] = []

    user = AuthenticatedUser(uid=user_uid, email="rate@test.local")
    app.dependency_overrides[get_current_user] = lambda: user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First 10 requests succeed
        for i in range(10):
            res = await client.post(
                "/v1/nursebot/ask",
                json={"question": f"Question {i} about MedBot?"},
            )
            assert res.status_code == 200

        # 11th request triggers 429
        res11 = await client.post(
            "/v1/nursebot/ask",
            json={"question": "Question 11 - should be blocked"},
        )
        assert res11.status_code == 429
        assert "Rate limit exceeded" in res11.json()["detail"]


@pytest.mark.anyio
async def test_nursebot_ask_no_database_transcripts():
    """Zero chat transcripts or records written to database during ask interactions."""
    user = AuthenticatedUser(uid="user_audit_tester", email="audit@test.local")
    app.dependency_overrides[get_current_user] = lambda: user

    db = TestingSessionLocal()
    initial_profiles = db.query(UserProfile).count()
    initial_summaries = db.query(SavedSummary).count()
    initial_tasks = db.query(CarePlanItem).count()
    initial_consents = db.query(UserConsentLog).count()
    db.close()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/v1/nursebot/ask", json={"question": "chest pain"})
        await client.post("/v1/nursebot/ask", json={"question": "diagnose me"})
        await client.post("/v1/nursebot/ask", json={"question": "how does explorer work?"})

    db2 = TestingSessionLocal()
    assert db2.query(UserProfile).count() == initial_profiles
    assert db2.query(SavedSummary).count() == initial_summaries
    assert db2.query(CarePlanItem).count() == initial_tasks
    assert db2.query(UserConsentLog).count() == initial_consents
    db2.close()

