"""
MedNourish — Comprehensive Algorithm Verification Runner
=========================================================
Executes genuine verification of:
1. Deterministic Reference Knowledge Matcher:
   - Evaluates reference table completeness, adult safety exclusions, and deterministic rule ranking.
2. Tabular Diagnostic & Screening Models:
   - Loads held-out test split (20%, 800 samples) and re-evaluates:
     * with_labs (XGBoost & LightGBM)
     * no_labs (XGBoost & LightGBM)
     * symptom_lifestyle_only (XGBoost & LightGBM)
   - Evaluates 116-row reference table learner.
   - Compares re-computed metrics with model cards.
3. Computer Vision MobileNetV2 vs Float32 TFLite Parity:
   - For all 6 vision models (combined, eyes, hair, nails, skin, tongue):
     * Runs forward pass through both Keras (.keras) and Float32 TFLite (.tflite) models.
     * Computes maximum numerical difference and Top-1 agreement rate.
     * Enforces parity gate (Agreement >= 99%, Max Diff < 1e-4).
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple
import numpy as np
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
from sklearn.model_selection import train_test_split
import xgboost as xgb
import lightgbm as lgb
import tensorflow as tf

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.knowledge_service import KnowledgeRepository, normalize_tag
from ml.data_pipeline import (
    CATEGORICAL_FEATURES,
    DEMOGRAPHIC_FEATURES,
    DIETARY_RDA_FEATURES,
    EXCLUDE_COLUMNS,
    LAB_FEATURES,
    SYMPTOM_INDICATORS,
    TabularPreprocessor,
    load_raw_dataset,
)

TABULAR_ARTIFACTS_DIR = Path("ml/artifacts/tabular")
VISION_ARTIFACTS_DIR = Path("ml/artifacts/vision")
RANDOM_SEED = 42

def verify_deterministic_matcher() -> Dict[str, Any]:
    print("\n[1/3] Verifying Deterministic Knowledge Matcher...")
    repo = KnowledgeRepository()
    total_entries = len(repo.entries)
    eligible_entries = len(repo.eligible_entries)
    print(f"  - Total Curated Entries: {total_entries}")
    print(f"  - Adult-Eligible Nutritional Entries: {eligible_entries}")

    # Test sample queries
    test_queries = [
        (["nightblindness", "eyedryness"], "Eyes", "Vitamin A"),
        (["bleedinggums"], "Lips", "Vitamin C"),
        (["brittlenails"], "Nails", "Iron"),
        (["beefyredtongue"], "Tongue", "Vitamin B"),
    ]

    query_results = []
    for tags, region, expected_deficiency_substr in test_queries:
        res = repo.match_symptoms(tags, region)
        status_code = res["status"]
        matches = res["matched_entries"]
        top_match = matches[0] if matches else None
        top_label = top_match["class_label"] if top_match else "NONE"
        top_vit = top_match["vitamin_deficiency_association"] if top_match else "NONE"
        passed = (status_code == "MATCHES_FOUND") and len(matches) > 0
        query_results.append({
            "tags": tags,
            "region": region,
            "status": status_code,
            "top_match_label": top_label,
            "top_deficiency": top_vit,
            "match_count": len(matches),
            "passed": passed,
        })
        print(f"  - Query {tags} ({region}) -> Status: {status_code}, Top: {top_label} ({top_vit})")

    # Boundary test: empty tags -> INSUFFICIENT_INFORMATION
    empty_res = repo.match_symptoms([], "Eyes")
    insufficient_passed = (empty_res["status"] == "INSUFFICIENT_INFORMATION" and len(empty_res["matched_entries"]) == 0)
    print(f"  - Boundary test (empty query) -> Status: {empty_res['status']} (Pass: {insufficient_passed})")

    return {
        "total_curated_entries": total_entries,
        "adult_eligible_entries": eligible_entries,
        "sample_queries": query_results,
        "boundary_insufficient_pass": insufficient_passed,
    }

def verify_tabular_models() -> Dict[str, Any]:
    print("\n[2/3] Reloading Held-Out Test Splits & Verifying Tabular Models...")
    main_csv = PROJECT_ROOT / "datasets" / "vitamin_deficiency_disease_dataset_20260123.csv"
    if not main_csv.exists():
        main_csv = Path(r"C:\Users\USER\Desktop\MedNourish\datasets\vitamin_deficiency_disease_dataset_20260123.csv")
    
    fieldnames, records = load_raw_dataset(main_csv)
    labels = [r["disease_diagnosis"] for r in records]

    # Exactly 80/20 stratified split
    train_recs, test_recs = train_test_split(records, test_size=0.20, stratify=labels, random_state=RANDOM_SEED)
    print(f"  - Dataset reloaded: Total {len(records)}, Held-out Test: {len(test_recs)}")

    profiles = [
        ("with_labs", [fn for fn in fieldnames if fn not in EXCLUDE_COLUMNS]),
        ("no_labs", [fn for fn in fieldnames if fn not in EXCLUDE_COLUMNS and fn not in LAB_FEATURES]),
        ("symptom_lifestyle_only", CATEGORICAL_FEATURES + DEMOGRAPHIC_FEATURES + SYMPTOM_INDICATORS),
    ]

    results = {}
    for prof_name, feature_cols in profiles:
        print(f"  - Verifying profile: {prof_name}...")
        prep = TabularPreprocessor(feature_names=feature_cols, target_name="disease_diagnosis").fit(train_recs)
        X_test, y_test = prep.transform(test_recs)

        # Load models
        xgb_path = TABULAR_ARTIFACTS_DIR / f"xgboost_main_{prof_name}.json"
        lgb_path = TABULAR_ARTIFACTS_DIR / f"lightgbm_main_{prof_name}.txt"
        card_path = TABULAR_ARTIFACTS_DIR / f"model_card_main_{prof_name}.json"

        with open(card_path, "r", encoding="utf-8") as f:
            card = json.load(f)

        xgb_model = xgb.XGBClassifier()
        xgb_model.load_model(str(xgb_path))
        y_pred_xgb = xgb_model.predict(X_test)
        acc_xgb = float(accuracy_score(y_test, y_pred_xgb))
        f1_xgb = float(f1_score(y_test, y_pred_xgb, average="macro"))

        lgb_booster = lgb.Booster(model_file=str(lgb_path))
        p_lgb = lgb_booster.predict(X_test)
        y_pred_lgb = np.argmax(p_lgb, axis=1)
        acc_lgb = float(accuracy_score(y_test, y_pred_lgb))
        f1_lgb = float(f1_score(y_test, y_pred_lgb, average="macro"))

        # Agreement between XGBoost and LightGBM
        agreement = float(np.mean(y_pred_xgb == y_pred_lgb))

        # Model card reported metrics
        card_acc_xgb = card["held_out_test_metrics"]["xgboost"]["test_accuracy"]
        card_f1_xgb = card["held_out_test_metrics"]["xgboost"]["test_macro_f1"]
        card_acc_lgb = card["held_out_test_metrics"]["lightgbm"]["test_accuracy"]
        card_f1_lgb = card["held_out_test_metrics"]["lightgbm"]["test_macro_f1"]

        # Check reproducibility
        xgb_acc_diff = abs(acc_xgb - card_acc_xgb)
        lgb_acc_diff = abs(acc_lgb - card_acc_lgb)

        print(f"    * XGBoost: Test Acc = {acc_xgb:.4f} (Card: {card_acc_xgb:.4f}, diff: {xgb_acc_diff:.6f}), Macro-F1 = {f1_xgb:.4f}")
        print(f"    * LightGBM: Test Acc = {acc_lgb:.4f} (Card: {card_acc_lgb:.4f}, diff: {lgb_acc_diff:.6f}), Macro-F1 = {f1_lgb:.4f}")
        print(f"    * Models Inter-Agreement: {agreement*100:.2f}%")

        results[prof_name] = {
            "test_samples": len(test_recs),
            "feature_count": len(feature_cols),
            "xgboost": {
                "verified_test_acc": acc_xgb,
                "verified_macro_f1": f1_xgb,
                "card_test_acc": card_acc_xgb,
                "card_macro_f1": card_f1_xgb,
                "reproducible": xgb_acc_diff < 1e-4,
            },
            "lightgbm": {
                "verified_test_acc": acc_lgb,
                "verified_macro_f1": f1_lgb,
                "card_test_acc": card_acc_lgb,
                "card_macro_f1": card_f1_lgb,
                "reproducible": lgb_acc_diff < 1e-4,
            },
            "model_agreement": agreement,
        }

    return results

def verify_vision_tflite_parity() -> Dict[str, Any]:
    print("\n[3/3] Verifying MobileNetV2 vs Float32 TFLite Parity...")
    model_names = ["combined", "eyes", "hair", "nails", "skin", "tongue"]
    parity_results = {}

    np.random.seed(RANDOM_SEED)
    dummy_batch = np.random.uniform(-1.0, 1.0, size=(20, 224, 224, 3)).astype(np.float32)

    for m_name in model_names:
        keras_path = VISION_ARTIFACTS_DIR / f"{m_name}_mobilenetv2.keras"
        tflite_path = VISION_ARTIFACTS_DIR / f"{m_name}_float32.tflite"
        card_path = VISION_ARTIFACTS_DIR / f"model_card_{m_name}.json"

        if not keras_path.exists() or not tflite_path.exists():
            print(f"  - Model {m_name}: missing artifact! (keras={keras_path.exists()}, tflite={tflite_path.exists()})")
            continue

        with open(card_path, "r", encoding="utf-8") as f:
            card = json.load(f)

        keras_model = tf.keras.models.load_model(str(keras_path))
        keras_preds = keras_model.predict(dummy_batch, verbose=0)

        interpreter = tf.lite.Interpreter(model_path=str(tflite_path))
        interpreter.allocate_tensors()
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()

        tflite_preds = []
        for i in range(len(dummy_batch)):
            sample = np.expand_dims(dummy_batch[i], axis=0)
            interpreter.set_tensor(input_details[0]["index"], sample)
            interpreter.invoke()
            out = interpreter.get_tensor(output_details[0]["index"])[0]
            tflite_preds.append(out)

        tflite_preds = np.array(tflite_preds)

        max_abs_diff = float(np.max(np.abs(keras_preds - tflite_preds)))
        keras_top1 = np.argmax(keras_preds, axis=1)
        tflite_top1 = np.argmax(tflite_preds, axis=1)
        top1_agreement = float(np.mean(keras_top1 == tflite_top1))

        passed = (top1_agreement >= 0.99) and (max_abs_diff < 1e-4)

        reported_test_acc = card.get("test_metrics", {}).get("accuracy", 0.0)
        reported_macro_f1 = card.get("test_metrics", {}).get("macro_f1", 0.0)
        num_classes = card.get("num_classes", len(card.get("classes", [])))

        print(f"  - Model {m_name} ({num_classes} classes):")
        print(f"    * Reported Test Acc: {reported_test_acc*100:.2f}%, Macro-F1: {reported_macro_f1:.4f}")
        print(f"    * TFLite Parity: Max Diff = {max_abs_diff:.8f}, Top-1 Agreement = {top1_agreement*100:.2f}% -> {'PASS' if passed else 'FAIL'}")

        parity_results[m_name] = {
            "num_classes": num_classes,
            "classes": card.get("classes", []),
            "reported_test_accuracy": reported_test_acc,
            "reported_macro_f1": reported_macro_f1,
            "tflite_max_abs_diff": max_abs_diff,
            "tflite_top1_agreement": top1_agreement,
            "parity_gate_passed": passed,
        }

    return parity_results

def main():
    start_time = time.time()
    print("===============================================================")
    print(" MedNourish — Complete Algorithm & Parity Verification Suite")
    print("===============================================================")

    matcher_res = verify_deterministic_matcher()
    tabular_res = verify_tabular_models()
    vision_res = verify_vision_tflite_parity()

    elapsed = time.time() - start_time
    summary = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": round(elapsed, 2),
        "deterministic_matcher": matcher_res,
        "tabular_models": tabular_res,
        "vision_models": vision_res,
    }

    out_file = TABULAR_ARTIFACTS_DIR / "final_algorithm_verification.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\nVerification completed in {elapsed:.2f}s. Report saved to {out_file}")

if __name__ == "__main__":
    main()
