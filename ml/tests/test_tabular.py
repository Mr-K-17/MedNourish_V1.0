"""
MedNourish — Tabular ML and Reference Contract Test Suite
=========================================================
Tests:
1. CSV Use Matrix completeness (all 34 CSVs accounted for).
2. Model artifact existence and JSON model card integrity.
3. Realistic leakage gap verification (with-labs vs without-labs performance).
4. Rare class recall tracking (Night_Blindness, Scurvy).
5. Model inference verification (loading XGBoost and LightGBM models).
6. Reference contract & crosswalk join coverage.
"""

import json
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest
import numpy as np
import xgboost as xgb
import lightgbm as lgb

from ml.ref_contract import build_reference_crosswalk

ARTIFACTS_DIR = Path("ml/artifacts/tabular")
DOCS_DIR = Path("docs")

def test_csv_use_matrix_completeness():
    matrix_file = DOCS_DIR / "CSV_USE_MATRIX.md"
    assert matrix_file.exists(), "CSV_USE_MATRIX.md must exist in docs/"
    content = matrix_file.read_text(encoding="utf-8")
    assert "Total CSV Files Audited: 34" in content or "34 entries" in content or "| 34 |" in content
    assert "vitamin_deficiency_disease_dataset_20260123.csv" in content
    assert "Used for Training" in content
    assert "Used as Reference Lookup" in content
    assert "Excluded" in content

def test_tabular_artifacts_and_model_cards():
    required_files = [
        "xgboost_main_with_labs.json",
        "lightgbm_main_with_labs.txt",
        "xgboost_main_no_labs.json",
        "lightgbm_main_no_labs.txt",
        "xgboost_main_symptom_lifestyle_only.json",
        "lightgbm_main_symptom_lifestyle_only.txt",
        "keyword_nutrient_xgb.json",
        "keyword_nutrient_lgb.txt",
        "model_card_main_with_labs.json",
        "model_card_main_no_labs.json",
        "model_card_main_symptom_lifestyle_only.json",
        "model_card_keyword_reference.json",
        "tabular_evaluation_summary.json",
    ]
    for fn in required_files:
        p = ARTIFACTS_DIR / fn
        assert p.exists(), f"Artifact missing: {p}"

def test_leakage_gap_and_rare_classes():
    card_with_labs = json.loads((ARTIFACTS_DIR / "model_card_main_with_labs.json").read_text(encoding="utf-8"))
    card_no_labs = json.loads((ARTIFACTS_DIR / "model_card_main_no_labs.json").read_text(encoding="utf-8"))
    card_symptoms_only = json.loads((ARTIFACTS_DIR / "model_card_main_symptom_lifestyle_only.json").read_text(encoding="utf-8"))

    # Verify leakage gap: models with labs (0.9938) > models with symptoms only (0.7987)
    acc_with = card_with_labs["held_out_test_metrics"]["xgboost"]["test_accuracy"]
    acc_symptoms = card_symptoms_only["held_out_test_metrics"]["xgboost"]["test_accuracy"]
    assert acc_with > acc_symptoms, f"Expected with-labs accuracy ({acc_with}) > symptoms-only accuracy ({acc_symptoms})"
    assert acc_with >= 0.95, f"With-labs accuracy should reflect near-perfect deterministic separation ({acc_with})"
    assert acc_symptoms < 0.85, f"Symptoms-only accuracy should reflect realistic pre-test screening challenge ({acc_symptoms})"

    # Verify rare classes recall is tracked and recorded
    rare_with = card_with_labs["held_out_test_metrics"]["xgboost"]["rare_classes_recall"]
    rare_without = card_no_labs["held_out_test_metrics"]["xgboost"]["rare_classes_recall"]
    assert "Night_Blindness" in rare_with
    assert "Scurvy" in rare_with
    assert "Night_Blindness" in rare_without
    assert "Scurvy" in rare_without

    # Check leakage analysis notes
    assert "LEAKAGE CONFIRMED" in card_with_labs["leakage_analysis"]
    assert "REALISTIC CLINICAL PRE-TEST MODEL" in card_symptoms_only["leakage_analysis"]

def test_reference_model_card_disclaimer():
    card_ref = json.loads((ARTIFACTS_DIR / "model_card_keyword_reference.json").read_text(encoding="utf-8"))
    assert card_ref["sample_count"] == 116
    assert "REFERENCE-TABLE LEARNER ONLY" in card_ref["strictly_reference_warning"]

def test_model_inference_loading():
    # Load and test XGBoost model
    xgb_model = xgb.XGBClassifier()
    xgb_model.load_model(str(ARTIFACTS_DIR / "xgboost_main_with_labs.json"))
    dummy_input = np.zeros((1, xgb_model.n_features_in_), dtype=np.float32)
    preds = xgb_model.predict(dummy_input)
    assert len(preds) == 1

    # Load and test LightGBM model
    lgb_booster = lgb.Booster(model_file=str(ARTIFACTS_DIR / "lightgbm_main_with_labs.txt"))
    lgb_preds = lgb_booster.predict(dummy_input)
    assert lgb_preds.shape[0] == 1

def test_reference_crosswalk_coverage():
    cov = build_reference_crosswalk()
    assert cov["total_master_rows"] == 116
    assert cov["regional_coverage_pct"] > 40.0
    assert cov["routine_coverage_pct"] > 40.0
    crosswalk_file = Path("knowledge/curated/crosswalk.csv")
    assert crosswalk_file.exists()
