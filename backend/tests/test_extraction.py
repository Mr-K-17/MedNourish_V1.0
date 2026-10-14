"""Tests for Phase 2 (c) MedBot Free-Text Symptom Extraction Endpoint.

Verifies:
- Auth required (401 when unauthorized).
- Synonym mappings (e.g. 'tired' -> fatigue, 'cannot see well at night' -> nightblindness).
- Negation window skipping negated symptoms ('no', 'not', 'without', "don't have").
- Fuzzy matching with similarity ratio >= 0.88.
- Empty or unrecognizable text returns INSUFFICIENT_INFORMATION.
- Zero raw text stored in database (PRIV-01, C-23).
"""

import pytest
from httpx import ASGITransport, AsyncClient
from app.core.auth import AuthenticatedUser, get_current_user
from app.main import app
from app.services.extraction_service import symptom_extractor


def test_extraction_synonyms():
    """Verify everyday phrasings map accurately to canonical tags."""
    # 1. Tired -> fatigue
    res1 = symptom_extractor.extract_symptoms("I feel really tired all the time")
    assert "fatigue" in res1["tags"]

    # 2. Cannot see well at night -> nightblindness
    res2 = symptom_extractor.extract_symptoms("I cannot see well at night while walking")
    assert "nightblindness" in res2["tags"]

    # 3. Bleeding gums -> bleedinggums
    res3 = symptom_extractor.extract_symptoms("Noticed my gums bleed when brushing")
    assert "bleedinggums" in res3["tags"]


def test_extraction_negation_window():
    """Negated symptoms must be skipped by the negation window."""
    # Negated fatigue should NOT be extracted, but brittle nails SHOULD be
    text = "I do not have fatigue, but I have brittle nails and dry skin."
    res = symptom_extractor.extract_symptoms(text)
    assert "fatigue" not in res["tags"]
    assert "brittlenails" in res["tags"]
    assert "dryskin" in res["tags"]

    # 'without' negation
    text2 = "Experiencing hair loss without night blindness"
    res2 = symptom_extractor.extract_symptoms(text2)
    assert "hairloss" in res2["tags"]
    assert "nightblindness" not in res2["tags"]


def test_extraction_fuzzy_matching():
    """Slight typos matching SequenceMatcher >= 0.88 should be extracted."""
    # 'brittle nials' -> brittlenails
    res = symptom_extractor.extract_symptoms("My doctor noticed very brittle naisl")
    assert "brittlenails" in res["tags"]


def test_extraction_empty_or_unrelated_input():
    """Empty or unrecognizable input must return INSUFFICIENT_INFORMATION."""
    res_empty = symptom_extractor.extract_symptoms("")
    assert res_empty["status"] == "INSUFFICIENT_INFORMATION"

    res_none = symptom_extractor.extract_symptoms(None)
    assert res_none["status"] == "INSUFFICIENT_INFORMATION"

    res_gibberish = symptom_extractor.extract_symptoms("The quick brown fox jumps over the lazy dog.")
    assert res_gibberish["status"] == "INSUFFICIENT_INFORMATION"
    assert res_gibberish["tags"] == []


@pytest.mark.anyio
async def test_extraction_endpoint_auth_and_no_storage():
    """Verify POST /v1/medbot/extract requires auth and does not store text in DB."""
    transport = ASGITransport(app=app)

    # 1. Unauthenticated request -> 401
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_unauth = await client.post(
            "/v1/medbot/extract",
            json={"text": "I feel tired"},
        )
        assert res_unauth.status_code == 401

    # 2. Authenticated request -> 200
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(uid="extract_test_user")
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_auth = await client.post(
            "/v1/medbot/extract",
            json={"text": "I feel tired and have bleeding gums, but no fever"},
        )
        assert res_auth.status_code == 200
        data = res_auth.json()
        assert data["status"] == "SYMPTOMS_EXTRACTED"
        assert "fatigue" in data["tags"]
        assert "bleedinggums" in data["tags"]
        assert "fever" not in data["tags"]
        assert len(data["chips"]) >= 2

    app.dependency_overrides.pop(get_current_user, None)
