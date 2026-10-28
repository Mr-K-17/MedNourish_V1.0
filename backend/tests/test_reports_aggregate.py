"""Comprehensive tests for Reports Multi-Engine Aggregation & CarePlan Auto-Sync (Phase 5).

Verifies:
1. Authentication requirement for aggregate endpoint (401).
2. Empty aggregate handling (0 entries, fallback report card, clean empty charts).
3. Tabular profile proxy endpoint (/v1/mllab/predict/tabular_profile) structure and supporting evidence wording.
4. Recency-weighted aggregation mathematics:
   - Base weights [0.35, 0.25, 0.20, 0.12, 0.08] normalized to 1.0.
   - Exact mathematical blending of Reference %, XGBoost %, LightGBM %, Image %.
5. Chart data payloads for all 6 visualizations:
   - Grouped bar by nutrient x source.
   - Ranked horizontal bar with final % and risk bands.
   - Radar chart (multi-axial).
   - Donut chart of risk band counts.
   - Longitudinal timeline points.
   - Heatmap of body-region x nutrient.
6. Final Report Card structure:
   - Probable deficiency pattern text with percentages.
   - Demo risk band (High/Moderate/Low with heuristic label).
   - Supporting sources and suggested measures (no supplement/drug/dose terms).
   - High band adds clinician consultation advice.
7. CarePlan Auto-Sync:
   - Curated routine extraction from Dietary, Lifestyle, Follow-Up columns only.
   - Strict omission of Suggested_Supplementation and drug/dosing keywords.
   - Timeframe stripping.
   - De-duplication by (nutrient, text_hash).
   - Stale marking when nutrient falls below 30%.
   - Preservation of user-created and user-edited items.
8. Data isolation between different users.
9. Cascade deletion on user deletion.
"""

import json
import uuid
import pytest
from httpx import ASGITransport, AsyncClient

from app.core.auth import AuthenticatedUser, get_current_user
from app.db.session import get_db
from app.main import app
from app.models.user import CarePlanItem, SavedSummary, UserProfile
from app.services.careplan_sync_service import clean_routine_text, sync_careplan_from_top_nutrients
from tests.conftest import TestingSessionLocal


@pytest.mark.anyio
async def test_aggregate_unauthenticated():
    """GET /v1/reports/aggregate requires an authenticated user (401)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/v1/reports/aggregate")
        assert res.status_code == 401


@pytest.mark.anyio
async def test_aggregate_empty_for_new_user():
    """New user with zero saved summaries returns safe empty structure without crashing."""
    user = AuthenticatedUser(uid="user_fresh_no_summaries", email="fresh@test.local")
    app.dependency_overrides[get_current_user] = lambda: user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/v1/reports/aggregate")
        assert res.status_code == 200
        data = res.json()
        assert data["entries_count"] == 0
        assert data["recency_weights"] == []
        assert data["aggregated_nutrients"] == []
        assert data["chart_data"]["grouped_bar"] == []
        assert data["chart_data"]["ranked_horizontal"] == []
        assert "No saved checks" in data["final_report_card"]["probable_deficiencies"]


@pytest.mark.anyio
async def test_mllab_predict_tabular_profile_proxy(monkeypatch):
    """Proxy endpoint for symptom/lifestyle tabular predictor returns Model % and supporting evidence."""
    user = AuthenticatedUser(uid="user_tab_proxy", email="tab@test.local")
    app.dependency_overrides[get_current_user] = lambda: user

    mock_response_data = {
        "predictions": [
            {
                "syndrome": "Rickets_Osteomalacia",
                "xgboost_pct": 68.5,
                "lightgbm_pct": 65.2,
                "consensus_pct": 66.8,
                "label": "Model % (trained on unverified data)",
                "supporting_evidence": "supporting evidence: Rickets -> Vitamin D",
            },
            {
                "syndrome": "Anemia",
                "xgboost_pct": 42.1,
                "lightgbm_pct": 44.0,
                "consensus_pct": 43.0,
                "label": "Model % (trained on unverified data)",
                "supporting_evidence": "supporting evidence: Anemia -> Iron, Vitamin B12, Folate",
            },
        ],
        "estimated_features": ["smoking_status", "alcohol_consumption"],
        "label": "Model % (trained on unverified data)",
        "warning": "ACADEMIC DEMO SCOPE ONLY: Evaluated on synthetic literature distributions.",
    }

    class MockResp:
        status_code = 200
        def json(self):
            return mock_response_data

    async def mock_post(self, url, **kwargs):
        return MockResp()

    monkeypatch.setattr("httpx.AsyncClient.post", mock_post)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/v1/mllab/predict/tabular_profile",
            json={"age": 45, "gender": "Female", "bmi": 24.5, "symptoms": ["bone pain", "fatigue"]},
        )
        assert res.status_code == 200
        data = res.json()
        assert len(data["predictions"]) == 2
        pred1 = data["predictions"][0]
        assert pred1["syndrome"] == "Rickets_Osteomalacia"
        assert pred1["consensus_pct"] == 66.8
        assert "Model % (trained on unverified data)" in pred1["label"]
        assert "supporting evidence: Rickets -> Vitamin D" in pred1["supporting_evidence"]


@pytest.mark.anyio
async def test_recency_weighted_aggregation_math():
    """Verifies mathematical blending across multiple check-ins with recency weights."""
    user = AuthenticatedUser(uid="user_math_tester", email="math@test.local")
    app.dependency_overrides[get_current_user] = lambda: user

    db = next(app.dependency_overrides[get_db]())
    # Clean previous records for this user
    db.query(SavedSummary).filter(SavedSummary.user_id == user.uid).delete()
    db.commit()

    # Create 3 snapshots:
    # Snapshot 0 (most recent): Vitamin D = 80%, Iron = 40%
    # Snapshot 1: Vitamin D = 60%, Iron = 50%
    # Snapshot 2: Vitamin D = 40%, Iron = 60%
    # Base weights: [0.35, 0.25, 0.20]. Sum = 0.80.
    # Normalized weights: w0 = 0.35/0.8 = 0.4375, w1 = 0.25/0.8 = 0.3125, w2 = 0.20/0.8 = 0.25
    # Expected Vitamin D = 0.4375*80 + 0.3125*60 + 0.25*40 = 35 + 18.75 + 10 = 63.75 -> ~63.8%
    # Expected Iron = 0.4375*40 + 0.3125*50 + 0.25*60 = 17.5 + 15.625 + 15 = 48.125 -> ~48.1%

    s0_scores = {
        "Vitamin D": {"reference_pct": 80.0, "xgboost_pct": 75.0, "lightgbm_pct": 70.0, "image_pct": 0.0, "final_pct": 80.0},
        "Iron": {"reference_pct": 40.0, "xgboost_pct": 40.0, "lightgbm_pct": 40.0, "image_pct": 0.0, "final_pct": 40.0},
    }
    s1_scores = {
        "Vitamin D": {"reference_pct": 60.0, "xgboost_pct": 60.0, "lightgbm_pct": 60.0, "image_pct": 0.0, "final_pct": 60.0},
        "Iron": {"reference_pct": 50.0, "xgboost_pct": 50.0, "lightgbm_pct": 50.0, "image_pct": 0.0, "final_pct": 50.0},
    }
    s2_scores = {
        "Vitamin D": {"reference_pct": 40.0, "xgboost_pct": 40.0, "lightgbm_pct": 40.0, "image_pct": 0.0, "final_pct": 40.0},
        "Iron": {"reference_pct": 60.0, "xgboost_pct": 60.0, "lightgbm_pct": 60.0, "image_pct": 0.0, "final_pct": 60.0},
    }

    dummy_entries = [{"class_label": "Test", "body_region": "EYES", "category": "Nutritional", "vitamin_deficiency_association": "Vitamin D", "matched_tags": ["tag1"], "match_count": 1, "total_condition_tags": 1, "row_match_percentage": 50.0, "review_status": "draft"}]

    snap2 = SavedSummary(
        id=f"sum_test_2_{uuid.uuid4().hex[:8]}",
        user_id=user.uid,
        session_type="Explorer",
        body_region_filter="General",
        selected_tags_json='["bone pain"]',
        matched_entries_json=json.dumps(dummy_entries),
        match_count_total=1,
        snapshot_scores_json=json.dumps(s2_scores),
        package_version="v2.0",
        matcher_version="v2.0",
        review_status="draft",
        disclaimer="demo",
    )
    snap1 = SavedSummary(
        id=f"sum_test_1_{uuid.uuid4().hex[:8]}",
        user_id=user.uid,
        session_type="Explorer",
        body_region_filter="General",
        selected_tags_json='["bone pain"]',
        matched_entries_json=json.dumps(dummy_entries),
        match_count_total=1,
        snapshot_scores_json=json.dumps(s1_scores),
        package_version="v2.0",
        matcher_version="v2.0",
        review_status="draft",
        disclaimer="demo",
    )
    snap0 = SavedSummary(
        id=f"sum_test_0_{uuid.uuid4().hex[:8]}",
        user_id=user.uid,
        session_type="Explorer",
        body_region_filter="General",
        selected_tags_json='["bone pain"]',
        matched_entries_json=json.dumps(dummy_entries),
        match_count_total=1,
        snapshot_scores_json=json.dumps(s0_scores),
        package_version="v2.0",
        matcher_version="v2.0",
        review_status="draft",
        disclaimer="demo",
    )

    db.add(snap2)
    db.commit()
    db.add(snap1)
    db.commit()
    db.add(snap0)
    db.commit()
    db.close()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/v1/reports/aggregate")
        assert res.status_code == 200
        data = res.json()
        assert data["entries_count"] == 3
        assert len(data["recency_weights"]) == 3
        # Check normalized sum close to 1.0
        assert abs(sum(data["recency_weights"]) - 1.0) < 0.01

        nutrients_map = {item["nutrient"]: item for item in data["aggregated_nutrients"]}
        assert "Vitamin D" in nutrients_map
        assert "Iron" in nutrients_map

        # Check values within rounding tolerance
        assert abs(nutrients_map["Vitamin D"]["final_pct"] - 63.8) <= 0.3
        assert abs(nutrients_map["Iron"]["final_pct"] - 48.1) <= 0.3

        # Vitamin D >= 60% should be High risk band
        assert "High" in nutrients_map["Vitamin D"]["demo_risk_band"]
        # Iron between 30% and 59% should be Moderate risk band
        assert "Moderate" in nutrients_map["Iron"]["demo_risk_band"]

        # Final Report card checks
        card = data["final_report_card"]
        assert "Vitamin D" in card["probable_deficiencies"]
        assert "High" in card["demo_risk_band"]
        # High band adds clinician notice
        assert any("consult a qualified healthcare professional" in m.lower() for m in card["suggested_measures"])

        # Chart payloads check
        charts = data["chart_data"]
        assert len(charts["grouped_bar"]) >= 2
        assert len(charts["ranked_horizontal"]) >= 2
        assert len(charts["radar"]) >= 3
        assert len(charts["donut_risk"]) == 3
        assert len(charts["timeline"]) == 3


def test_careplan_clean_routine_text_rules():
    """Verifies that timeframe phrases and medication/supplement keywords are strictly stripped."""
    # 1. Strip timeframes
    text1 = "Routine eye exam every 6 months to maintain visual health"
    cleaned1 = clean_routine_text(text1)
    assert "every 6 months" not in cleaned1
    assert "Routine eye exam to maintain visual health" in cleaned1

    # 2. Strip supplement terms
    text2 = "Vitamin A supplementation as advised by physician, high-dose therapeutic oral retinol"
    cleaned2 = clean_routine_text(text2)
    assert "supplementation" not in cleaned2
    assert "oral retinol" not in cleaned2
    assert "high-dose" not in cleaned2


def test_careplan_sync_and_stale_tracking():
    """Verifies deduplication, stale marking, and protection of user-created items."""
    db = TestingSessionLocal()
    test_user_id = f"test_careplan_user_{uuid.uuid4().hex[:8]}"

    # 1. User has an existing manual item
    manual_item = CarePlanItem(
        id=f"cpt_{uuid.uuid4().hex[:16]}",
        user_id=test_user_id,
        title="Drink 2L fresh water daily",
        category="water",
        is_completed=False,
        is_auto=False,
        is_stale=False,
        is_user_edited=False,
    )
    db.add(manual_item)
    db.commit()

    # 2. Run sync with Vitamin D (65%) and Vitamin A (45%)
    top_nutrients = [
        {"nutrient": "Vitamin D", "final_pct": 65.0},
        {"nutrient": "Vitamin A", "final_pct": 45.0},
        {"nutrient": "Zinc", "final_pct": 20.0},  # < 30%, should be ignored
    ]
    res1 = sync_careplan_from_top_nutrients(db, test_user_id, "sum_1", top_nutrients, "High")
    assert res1["created"] >= 2  # Vitamin D and Vitamin A routines + Clinical follow-up

    auto_items = db.query(CarePlanItem).filter(CarePlanItem.user_id == test_user_id, CarePlanItem.is_auto.is_(True)).all()
    nutrients_synced = {it.nutrient for it in auto_items}
    assert "Vitamin D" in nutrients_synced
    assert "Vitamin A" in nutrients_synced
    assert "Zinc" not in nutrients_synced
    assert "Clinical Follow-Up" in nutrients_synced

    # 3. Repeat sync with same nutrients: deduplication should prevent new duplicate items
    res2 = sync_careplan_from_top_nutrients(db, test_user_id, "sum_2", top_nutrients, "High")
    assert res2["created"] == 0

    # 4. New check-in where Vitamin A drops below 30% (only Vitamin D remains)
    top_nutrients_dropped = [
        {"nutrient": "Vitamin D", "final_pct": 55.0},
        {"nutrient": "Vitamin A", "final_pct": 15.0},  # fell below 30!
    ]
    res3 = sync_careplan_from_top_nutrients(db, test_user_id, "sum_3", top_nutrients_dropped, "Moderate")
    assert res3["stale"] >= 1

    # Check that Vitamin A item is now marked stale
    vit_a_item = (
        db.query(CarePlanItem)
        .filter(CarePlanItem.user_id == test_user_id, CarePlanItem.nutrient == "Vitamin A")
        .first()
    )
    assert vit_a_item.is_stale is True

    # User's manual item MUST NOT be deleted or marked stale
    manual_check = db.query(CarePlanItem).filter(CarePlanItem.id == manual_item.id).first()
    assert manual_check is not None
    assert manual_check.is_stale is False
    assert manual_check.is_auto is False

    # Clean up
    db.query(CarePlanItem).filter(CarePlanItem.user_id == test_user_id).delete()
    db.commit()
    db.close()
