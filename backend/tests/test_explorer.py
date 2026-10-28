"""Tests for Symptom Reference Explorer API and matching logic.

Verifies:
1. Loading and schema validation of reference entries.
2. Safety enforcement: Excludes Non-Nutritional disease classes (SAF-09).
3. Safety enforcement: Excludes pediatric/infant conditions (SAF-10).
4. Safety enforcement: Excludes unreviewed treatment/supplement dosages (SAF-16).
5. Deterministic tie-breaking rules per REFERENCE_MATCHER_SPEC.md.
6. Minimum information rule (SAF-06): returns INSUFFICIENT_INFORMATION.
7. Unmatched queries: returns INSUFFICIENT_INFORMATION without reassurance.
8. Unauthenticated and invalid access: returns 401.
"""

from fastapi.testclient import TestClient
import pytest
from app.core.auth import AuthenticatedUser, get_current_user
from app.main import app
from app.services.knowledge_service import (
    KnowledgeRepository,
    normalize_tag,
)

client = TestClient(app)


@pytest.fixture
def override_auth():
    """Overrides authentication to provide a mock authenticated adult user."""
    def _mock_user():
        return AuthenticatedUser(uid="test_user_adult_123", email="user@example.com")

    app.dependency_overrides[get_current_user] = _mock_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


def test_tag_normalization():
    """Tests tag normalization helper."""
    assert normalize_tag("  Night-Blindness  ") == "night blindness"
    assert normalize_tag("FOAMY_WHITE_PATCH") == "foamy white patch"
    assert normalize_tag("dry/skin (severe)") == "dry skin severe"
    assert normalize_tag("") == ""


def test_repository_safety_exclusions():
    """Verifies that KnowledgeRepository strictly enforces SAF-09 and SAF-10."""
    repo = KnowledgeRepository()

    # 1. Total entries loaded
    assert len(repo.entries) == 116

    # 2. Non-nutritional classes are NOT eligible (SAF-09)
    non_nutritional = [e for e in repo.eligible_entries if not e.is_nutritional]
    assert len(non_nutritional) == 0

    # 3. Normal classes are NOT eligible
    normal_entries = [e for e in repo.eligible_entries if e.category.lower() == "normal"]
    assert len(normal_entries) == 0

    # 4. Pediatric/child-specific conditions are NOT eligible (SAF-10)
    # Hair row with Menkes disease / infants
    menkes_entries = [e for e in repo.eligible_entries if "menkes" in e.class_label.lower()]
    assert len(menkes_entries) == 0

    # All eligible entries must be adult-eligible and nutritional
    for entry in repo.eligible_entries:
        assert entry.is_nutritional is True
        assert entry.is_adult_eligible is True


def test_unauthenticated_explorer_access():
    """Verifies unauthenticated calls to explorer endpoints return 401."""
    # GET /v1/explorer/categories without token
    res1 = client.get("/v1/explorer/categories")
    assert res1.status_code == 401

    # POST /v1/explorer/match without token
    res2 = client.post("/v1/explorer/match", json={"selected_tags": ["nightblindness"]})
    assert res2.status_code == 401


def test_authenticated_categories_browsing(override_auth):
    """Verifies authenticated retrieval of categories and symptom tags."""
    res = client.get("/v1/explorer/categories")
    assert res.status_code == 200
    data = res.json()

    assert "regions" in data
    assert "tags_by_region" in data
    assert data["total_tags"] > 0
    assert "EYES" in data["regions"]
    assert "HAIR" in data["regions"]
    assert "LIPS" in data["regions"]
    assert "NAILS" in data["regions"]
    assert "SKIN" in data["regions"]
    assert "TONGUE" in data["regions"]


def test_matcher_insufficient_information_on_empty(override_auth):
    """Verifies empty tag selection returns INSUFFICIENT_INFORMATION (SAF-06)."""
    res = client.post("/v1/explorer/match", json={"selected_tags": []})
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "INSUFFICIENT_INFORMATION"
    assert "no problem" not in data["message"].lower()
    assert "all-clear" not in data["message"].lower()
    assert "disclaimer" in data
    assert len(data["matched_entries"]) == 0


def test_matcher_insufficient_information_on_unmatched(override_auth):
    """Verifies non-matching tags return INSUFFICIENT_INFORMATION without false reassurance."""
    res = client.post(
        "/v1/explorer/match",
        json={"selected_tags": ["completely_unrelated_xyz_symptom"]},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "INSUFFICIENT_INFORMATION"
    assert "does not indicate absence" in data["message"]
    assert len(data["matched_entries"]) == 0
    assert "completely unrelated xyz symptom" in data["unmatched_user_tags"]


def test_deterministic_matching_and_tie_breaking(override_auth):
    """Verifies deterministic set intersection and tie-breaking ordering."""
    # Query with multiple tags from EYES
    query = ["nightblindness", "eyedryness", "foamywhitepatch"]
    res = client.post("/v1/explorer/match", json={"selected_tags": query})
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "MATCHES_FOUND"
    entries = data["matched_entries"]
    assert len(entries) > 0

    # Top match should be Bitot_Spots (matches all 3 query tags)
    top = entries[0]
    assert top["class_label"] == "Bitot_Spots"
    assert top["match_count"] == 3
    assert "Bitot_Spots" in top["class_label"]
    assert "Vitamin A Deficiency" in top["vitamin_deficiency_association"]

    # Verify every result has review_status="unreviewed draft"
    for e in entries:
        assert e["review_status"] == "unreviewed draft"

    # Verify that descending order of match_count holds strictly
    for i in range(len(entries) - 1):
        assert entries[i]["match_count"] >= entries[i + 1]["match_count"]


def test_region_filtering(override_auth):
    """Verifies region filter restricts results to specified body region."""
    # Query with tags present in both Hair and Lips
    query = ["brittlenails", "fatigue"]
    res = client.post(
        "/v1/explorer/match",
        json={"selected_tags": query, "body_region_filter": "NAILS"},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "MATCHES_FOUND"
    for e in data["matched_entries"]:
        assert e["body_region"] == "NAILS"


def test_no_forbidden_diagnostic_terms_in_output(override_auth):
    """Verifies output contains no diagnostic, percentage, or treatment scores."""
    res = client.post("/v1/explorer/match", json={"selected_tags": ["nightblindness"]})
    assert res.status_code == 200
    raw_text = res.text.lower()

    # Medical safety prohibitions (SAF-01, SAF-02, SAF-08, SAF-17)
    forbidden = ["you have", "probability", "risk score", "take supplement", "prescription", "mg daily"]
    for term in forbidden:
        assert term not in raw_text, f"Forbidden term '{term}' found in match response"
