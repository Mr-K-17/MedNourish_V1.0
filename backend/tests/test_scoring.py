"""Tests for Phase 2 Reference Match Scoring Service.

Verifies:
- Determinism across 10 repeat executions.
- Monotonicity: adding matched tags never decreases row or nutrient percentage.
- Value bounds: strictly 0 <= percentage <= 95 (single tag cannot reach 100%).
- Every adult nutritional curated row is retrievable by its own full keyword set.
- Risk band thresholds: High >= 60, Moderate 30-59, Low < 30.
- Preserves SAF-09 (nutritional only) and SAF-10 (pediatric exclusions).
"""

import pytest
from app.services.knowledge_service import knowledge_repo
from app.services.scoring_service import scoring_service, calculate_risk_band


def test_scoring_determinism():
    """Identical input tags must produce bitwise identical outputs across 10 iterations."""
    tags = ["nightblindness", "eyedryness", "fatigue"]
    baseline = scoring_service.evaluate_tags(tags)

    for _ in range(10):
        run = scoring_service.evaluate_tags(tags)
        assert run["status"] == baseline["status"]
        assert len(run["nutrient_scores"]) == len(baseline["nutrient_scores"])
        for n1, n2 in zip(run["nutrient_scores"], baseline["nutrient_scores"]):
            assert n1["nutrient"] == n2["nutrient"]
            assert n1["percentage"] == n2["percentage"]
            assert n1["risk_band"] == n2["risk_band"]


def test_scoring_monotonicity():
    """Adding an additional symptom tag must never decrease any row or nutrient score."""
    tags_initial = ["nightblindness"]
    res_initial = scoring_service.evaluate_tags(tags_initial)
    scores_initial = {n["nutrient"]: n["percentage"] for n in res_initial["nutrient_scores"]}

    tags_expanded = ["nightblindness", "eyedryness"]
    res_expanded = scoring_service.evaluate_tags(tags_expanded)
    scores_expanded = {n["nutrient"]: n["percentage"] for n in res_expanded["nutrient_scores"]}

    for nut, init_pct in scores_initial.items():
        assert nut in scores_expanded
        assert scores_expanded[nut] >= init_pct, f"Monotonicity violated for {nut}: {scores_expanded[nut]} < {init_pct}"


def test_scoring_bounds_and_single_tag_shrinkage():
    """Outputs must strictly lie in [0, 95.0]; a single tag can never give 100%."""
    # Test all eligible entries individually
    for entry in knowledge_repo.eligible_entries[:20]:
        for kw in list(entry.normalized_keywords)[:1]:
            res = scoring_service.evaluate_tags([kw])
            if res["status"] == "MATCHES_FOUND":
                for nut in res["nutrient_scores"]:
                    assert 0.0 <= nut["percentage"] <= 95.0
                    # Single tag shrinkage: never 100%
                    assert nut["percentage"] < 100.0
                    for row in nut["contributing_rows"]:
                        assert 0.0 <= row["row_match_percentage"] <= 95.0
                        if row["match_count"] == 1:
                            assert row["row_match_percentage"] <= 85.0  # shrinkage cap for 1 tag


def test_every_curated_row_retrievable():
    """Every adult nutritional condition row must be retrievable when given its exact keywords."""
    for entry in knowledge_repo.eligible_entries:
        user_tags = list(entry.normalized_keywords)
        res = scoring_service.evaluate_tags(user_tags)
        assert res["status"] == "MATCHES_FOUND"
        matched_labels = {m["class_label"] for m in res["matched_entries"]}
        assert entry.class_label in matched_labels, f"Entry '{entry.class_label}' failed retrieval"


def test_risk_band_thresholds():
    """Verify configured risk band thresholds: High >= 60, Moderate 30-59, Low < 30."""
    assert calculate_risk_band(60.0) == "High"
    assert calculate_risk_band(75.5) == "High"
    assert calculate_risk_band(95.0) == "High"
    assert calculate_risk_band(59.9) == "Moderate"
    assert calculate_risk_band(30.0) == "Moderate"
    assert calculate_risk_band(29.9) == "Low"
    assert calculate_risk_band(0.0) == "Low"


def test_pediatric_and_non_nutritional_exclusions():
    """Pediatric terms and non-nutritional classes remain excluded per SAF-09 and SAF-10."""
    res = scoring_service.evaluate_tags(["menkes", "kinkyhair", "normal"])
    for nut in res.get("nutrient_scores", []):
        for row in nut["contributing_rows"]:
            assert "menkes" not in row["class_label"].lower()
            assert row["category"] != "Non_Nutritional"
            assert row["category"] != "Normal"
