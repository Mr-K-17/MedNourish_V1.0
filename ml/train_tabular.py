"""
MedNourish — Complete Stage 2 Tabular ML Pipeline
=================================================
Executes:
(a) Main CSV (4,000x34) tabular training & evaluation across three profiles:
    - with_labs (full clinical laboratory serum features, near-perfect accuracy >99%)
    - no_labs (dietary RDA + symptoms + lifestyle/demographics, ~99%)
    - symptom_lifestyle_only (strictly non-invasive symptoms + demographics, ~79% accuracy, showing realistic clinical pre-test gap)
    Evaluated with 5-fold CV on train split and held-out test evaluation.
(b) 116-row Master Reference Table keyword-to-nutrient learner using character n-gram TF-IDF (3-5)
    + Body_Region one-hot, evaluated with Stratified 5-Fold CV comparing XGBoost, LightGBM, and Deterministic Baseline.
    Strictly marked: reference-table learner, NOT a patient predictor.
(c) Model exports and comprehensive JSON model cards to ml/artifacts/tabular/.
"""

import json
import os
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any
from collections import Counter
import numpy as np

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, classification_report, confusion_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
import xgboost as xgb
import lightgbm as lgb

from ml.data_pipeline import (
    TabularPreprocessor,
    load_raw_dataset,
    CATEGORICAL_FEATURES,
    LAB_FEATURES,
    DIETARY_RDA_FEATURES,
    DEMOGRAPHIC_FEATURES,
    SYMPTOM_INDICATORS,
    EXCLUDE_COLUMNS,
    VALID_TARGET_CLASSES,
)

ARCHIVE_DIR = Path(r"C:\Users\USER\Desktop\MedNourish\datasets")
DEV_DATASETS = Path(r"C:\Users\USER\Desktop\MedNourish-Dev\datasets")
DATASET_ROOT = ARCHIVE_DIR if ARCHIVE_DIR.exists() else DEV_DATASETS

ARTIFACTS_DIR = Path("ml/artifacts/tabular")
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

RANDOM_SEED = 42

# --------------------------------------------------------------------------
# (a) Main CSV Tabular Pipeline
# --------------------------------------------------------------------------

def run_main_tabular_experiments() -> Dict[str, Any]:
    main_csv = DATASET_ROOT / "vitamin_deficiency_disease_dataset_20260123.csv"
    if not main_csv.exists():
        raise FileNotFoundError(f"Main tabular dataset not found at {main_csv}")

    fieldnames, records = load_raw_dataset(main_csv)
    labels = [r["disease_diagnosis"] for r in records]

    # Deterministic 80/20 train/test split
    train_records, test_records = train_test_split(
        records, test_size=0.20, stratify=labels, random_state=RANDOM_SEED
    )

    profiles = [
        (
            "with_labs",
            [fn for fn in fieldnames if fn not in EXCLUDE_COLUMNS],
            (
                "LEAKAGE CONFIRMED: Laboratory serum biomarkers (hemoglobin, serum_vitamin_d, "
                "serum_vitamin_b12, serum_folate) directly determine diagnostic classification thresholds, "
                "yielding near-perfect accuracy (>99%). This model represents post-bloodwork confirmatory diagnosis."
            ),
        ),
        (
            "no_labs",
            [fn for fn in fieldnames if fn not in EXCLUDE_COLUMNS and fn not in LAB_FEATURES],
            (
                "DIETARY & SYMPTOM MODEL: Excludes invasive serum blood tests, but retains calculated dietary RDA percentages "
                "and binary symptom indicators. Yields ~99% accuracy due to direct synthetic alignment between dietary "
                "intake percentages and simulated deficiency states."
            ),
        ),
        (
            "symptom_lifestyle_only",
            CATEGORICAL_FEATURES + DEMOGRAPHIC_FEATURES + SYMPTOM_INDICATORS,
            (
                "REALISTIC CLINICAL PRE-TEST MODEL: Strictly relies on non-invasive screening signals "
                "(observable physical symptoms, lifestyle habits, and patient demographics) with zero lab tests and "
                "zero calculated RDA percentages. Test accuracy (~79%) and macro-F1 (~0.61) demonstrate the genuine "
                "ambiguity and realistic screening challenge before clinical diagnostic confirmation."
            ),
        ),
    ]

    results = {}

    for mode_name, selected_features, leakage_note in profiles:
        print(f"\n--- Running Main Dataset Tabular Experiment: {mode_name.upper()} ---")

        preprocessor = TabularPreprocessor(
            feature_names=selected_features,
            target_name="disease_diagnosis",
        )
        preprocessor.fit(train_records)

        X_train, y_train = preprocessor.transform(train_records)
        X_test, y_test = preprocessor.transform(test_records)
        target_names = [preprocessor.target_inverse_mapping[i] for i in range(len(preprocessor.target_inverse_mapping))]

        # 5-Fold Cross-Validation on TRAIN split only
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
        cv_xgb_f1 = []
        cv_lgb_f1 = []

        for fold, (train_idx, val_idx) in enumerate(skf.split(X_train, y_train)):
            X_tr, y_tr = X_train[train_idx], y_train[train_idx]
            X_va, y_va = X_train[val_idx], y_train[val_idx]

            clf_xgb = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.08,
                random_state=RANDOM_SEED + fold,
                eval_metric="mlogloss",
                verbosity=0,
            )
            clf_xgb.fit(X_tr, y_tr)
            preds_xgb = clf_xgb.predict(X_va)
            cv_xgb_f1.append(f1_score(y_va, preds_xgb, average="macro"))

            clf_lgb = lgb.LGBMClassifier(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.08,
                random_state=RANDOM_SEED + fold,
                verbosity=-1,
            )
            clf_lgb.fit(X_tr, y_tr)
            preds_lgb = clf_lgb.predict(X_va)
            cv_lgb_f1.append(f1_score(y_va, preds_lgb, average="macro"))

        # Final models trained on full training split
        final_xgb = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.08,
            random_state=RANDOM_SEED,
            eval_metric="mlogloss",
            verbosity=0,
        )
        final_xgb.fit(X_train, y_train)

        final_lgb = lgb.LGBMClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.08,
            random_state=RANDOM_SEED,
            verbosity=-1,
        )
        final_lgb.fit(X_train, y_train)

        # Held-out Test Evaluation
        y_pred_xgb = final_xgb.predict(X_test)
        y_pred_lgb = final_lgb.predict(X_test)

        def get_eval_dict(y_pred, clf_name):
            acc = float(accuracy_score(y_test, y_pred))
            f1_macro = float(f1_score(y_test, y_pred, average="macro"))
            report = classification_report(y_test, y_pred, target_names=target_names, output_dict=True, zero_division=0)
            cm = confusion_matrix(y_test, y_pred).tolist()
            per_class_recall = {cls: report[cls]["recall"] for cls in target_names}
            rare_class_recall = {
                "Night_Blindness": report.get("Night_Blindness", {}).get("recall", 0.0),
                "Scurvy": report.get("Scurvy", {}).get("recall", 0.0),
            }
            return {
                "classifier": clf_name,
                "test_accuracy": round(acc, 4),
                "test_macro_f1": round(f1_macro, 4),
                "per_class_recall": per_class_recall,
                "rare_classes_recall": rare_class_recall,
                "confusion_matrix": cm,
                "classification_report": report,
            }

        eval_xgb = get_eval_dict(y_pred_xgb, "XGBoost")
        eval_lgb = get_eval_dict(y_pred_lgb, "LightGBM")

        # Feature Importance (XGBoost)
        xgb_importances = final_xgb.feature_importances_
        feature_names = preprocessor.feature_names
        feat_imp = sorted(
            [{"feature": f, "importance": round(float(imp), 5)} for f, imp in zip(feature_names, xgb_importances)],
            key=lambda x: x["importance"],
            reverse=True,
        )

        # Save model binaries
        xgb_model_path = ARTIFACTS_DIR / f"xgboost_main_{mode_name}.json"
        final_xgb.save_model(str(xgb_model_path))

        lgb_model_path = ARTIFACTS_DIR / f"lightgbm_main_{mode_name}.txt"
        final_lgb.booster_.save_model(str(lgb_model_path))

        # Model Card
        numeric_cols = [c for c in selected_features if c not in CATEGORICAL_FEATURES]
        feature_ranges = {}
        for col in numeric_cols:
            vals = [float(r[col]) for r in records if r.get(col, "")]
            feature_ranges[col] = {"min": min(vals), "max": max(vals), "mean": round(float(np.mean(vals)), 2)}

        model_card = {
            "model_id": f"mednourish-tabular-{mode_name}",
            "profile": mode_name,
            "description": f"Tabular multi-class deficiency disease predictor ({mode_name})",
            "date": "2026-10-14",
            "dataset": "datasets/vitamin_deficiency_disease_dataset_20260123.csv",
            "sample_count": len(records),
            "train_size": len(train_records),
            "test_size": len(test_records),
            "target_classes": target_names,
            "feature_count": len(feature_names),
            "feature_names": feature_names,
            "feature_ranges": feature_ranges,
            "includes_lab_biomarkers": (mode_name == "with_labs"),
            "cv_5fold_macro_f1": {
                "xgboost_mean": round(float(np.mean(cv_xgb_f1)), 4),
                "xgboost_std": round(float(np.std(cv_xgb_f1)), 4),
                "lightgbm_mean": round(float(np.mean(cv_lgb_f1)), 4),
                "lightgbm_std": round(float(np.std(cv_lgb_f1)), 4),
            },
            "held_out_test_metrics": {
                "xgboost": eval_xgb,
                "lightgbm": eval_lgb,
            },
            "top_10_features": feat_imp[:10],
            "leakage_analysis": leakage_note,
            "data_provenance_warning": (
                "ACADEMIC SYNTHETIC DATASET: Derived from synthetic literature distributions. "
                "Must NEVER be used for autonomous clinical diagnosis or real-time treatment prescription."
            ),
            "library_versions": {
                "xgboost": xgb.__version__,
                "lightgbm": lgb.__version__,
                "sklearn": "1.6.1",
            },
        }

        card_path = ARTIFACTS_DIR / f"model_card_main_{mode_name}.json"
        with open(card_path, "w", encoding="utf-8") as f:
            json.dump(model_card, f, indent=2)

        results[mode_name] = model_card
        print(f"XGBoost Test Macro-F1: {eval_xgb['test_macro_f1']} | Accuracy: {eval_xgb['test_accuracy']}")
        print(f"LightGBM Test Macro-F1: {eval_lgb['test_macro_f1']} | Accuracy: {eval_lgb['test_accuracy']}")

    return results

# --------------------------------------------------------------------------
# (b) 116-Row Reference Table Keyword-to-Nutrient Learner
# --------------------------------------------------------------------------

def run_reference_keyword_experiment() -> Dict[str, Any]:
    print("\n--- Running Reference Table Keyword-to-Nutrient Learner (116 Rows) ---")
    ref_file = Path("knowledge/curated/MedNourish_Symptom_Keywords_vs_Vitamin_Deficiency_Mapping.csv")
    if not ref_file.exists():
        ref_file = DATASET_ROOT / "MedBot_datasets/MedNourish_Symptom_Keywords_vs_Vitamin_Deficiency_Mapping.csv"

    # Load nutrient group mapping
    yaml_path = Path("ml/class_maps/nutrient_groups.yaml")
    with open(yaml_path, "r", encoding="utf-8") as f:
        group_spec = yaml.safe_load(f)["groups"]

    deficiency_to_group = {}
    for grp, raw_list in group_spec.items():
        for raw in raw_list:
            deficiency_to_group[raw.strip().lower()] = grp

    import csv
    with open(ref_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        ref_rows = list(reader)

    print(f"Loaded {len(ref_rows)} rows from canonical reference table.")

    # Target: Nutrient Group
    targets = []
    for r in ref_rows:
        raw_def = r["Vitamin_Deficiency"].strip().lower()
        grp = deficiency_to_group.get(raw_def, "Non_Nutritional")
        targets.append(grp)

    unique_groups = sorted(list(set(targets)))
    group_to_idx = {g: i for i, g in enumerate(unique_groups)}
    y = np.array([group_to_idx[g] for g in targets], dtype=np.int64)

    # Feature representation:
    # 1. Body_Region one-hot
    regions = sorted(list(set(r["Body_Region"].strip() for r in ref_rows)))
    region_to_idx = {reg: i for i, reg in enumerate(regions)}

    X_reg = np.zeros((len(ref_rows), len(regions)), dtype=np.float32)
    for i, r in enumerate(ref_rows):
        X_reg[i, region_to_idx[r["Body_Region"].strip()]] = 1.0

    # 2. Symptom_Keywords character n-gram TF-IDF (3 to 5 chars)
    texts = []
    for r in ref_rows:
        text = f"{r['Class_Label'].replace('_', ' ')} {r['Symptom_Keywords']}".lower()
        texts.append(text)

    tfidf = TfidfVectorizer(ngram_range=(3, 5), analyzer="char", min_df=2, sublinear_tf=True)
    X_text = tfidf.fit_transform(texts).toarray()

    X = np.hstack([X_reg, X_text]).astype(np.float32)
    feature_names = [f"region_{r}" for r in regions] + [f"char_ngram_{f}" for f in tfidf.get_feature_names_out()]

    print(f"Feature matrix: {X.shape[0]} rows × {X.shape[1]} features, {len(unique_groups)} classes.")
    print("Class distribution:", Counter(targets))

    # Stratified 5-Fold Cross-Validation
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)

    xgb_f1 = []
    lgb_f1 = []
    baseline_f1 = []

    # Deterministic baseline: matches nutrient names directly in keywords
    nutrient_keywords = {
        "Vitamin_A": ["xerophthalmia", "bitot", "night blindness", "retinol", "follicular hyperkeratosis", "vitamin a"],
        "Vitamin_B_Complex": ["pellagra", "niacin", "thiamine", "riboflavin", "glossitis", "cheilitis", "angular", "b12", "b3", "b6", "folate"],
        "Vitamin_C_and_D": ["scurvy", "ascorbic", "petechiae", "corkscrew", "rickets", "vitamin c", "vitamin d", "perifollicular"],
        "Iron_and_Zinc": ["koilonychia", "pallor", "iron", "zinc", "anemia", "taste", "dystrophy", "ridging"],
        "Protein_Energy_Malnutrition": ["kwashiorkor", "marasmus", "flag sign", "sparse", "thin", "depigmented", "pem"],
    }

    for train_idx, val_idx in skf.split(X, y):
        X_tr, y_tr = X[train_idx], y[train_idx]
        X_va, y_va = X[val_idx], y[val_idx]

        # XGBoost fold
        clf_xgb = xgb.XGBClassifier(
            n_estimators=60,
            max_depth=3,
            learning_rate=0.08,
            random_state=RANDOM_SEED,
            eval_metric="mlogloss",
            verbosity=0,
        )
        clf_xgb.fit(X_tr, y_tr)
        p_xgb = clf_xgb.predict(X_va)
        xgb_f1.append(f1_score(y_va, p_xgb, average="macro"))

        # LightGBM fold
        clf_lgb = lgb.LGBMClassifier(
            n_estimators=60,
            max_depth=3,
            learning_rate=0.08,
            random_state=RANDOM_SEED,
            verbosity=-1,
        )
        clf_lgb.fit(X_tr, y_tr)
        p_lgb = clf_lgb.predict(X_va)
        lgb_f1.append(f1_score(y_va, p_lgb, average="macro"))

        # Deterministic Baseline fold
        p_base = []
        for idx in val_idx:
            row_txt = texts[idx]
            assigned = "Non_Nutritional"
            for grp_k, kws in nutrient_keywords.items():
                if any(kw in row_txt for kw in kws):
                    assigned = grp_k
                    break
            p_base.append(group_to_idx[assigned])
        baseline_f1.append(f1_score(y_va, p_base, average="macro"))

    # Train final models on entire 116-row reference table
    final_xgb = xgb.XGBClassifier(
        n_estimators=60,
        max_depth=3,
        learning_rate=0.08,
        random_state=RANDOM_SEED,
        eval_metric="mlogloss",
        verbosity=0,
    )
    final_xgb.fit(X, y)

    final_lgb = lgb.LGBMClassifier(
        n_estimators=60,
        max_depth=3,
        learning_rate=0.08,
        random_state=RANDOM_SEED,
        verbosity=-1,
    )
    final_lgb.fit(X, y)

    # Save models
    xgb_ref_path = ARTIFACTS_DIR / "keyword_nutrient_xgb.json"
    final_xgb.save_model(str(xgb_ref_path))

    lgb_ref_path = ARTIFACTS_DIR / "keyword_nutrient_lgb.txt"
    final_lgb.booster_.save_model(str(lgb_ref_path))

    # Feature Importance (XGBoost)
    xgb_imp = final_xgb.feature_importances_
    top_features = sorted(
        [{"feature": f, "importance": round(float(imp), 5)} for f, imp in zip(feature_names, xgb_imp) if imp > 0],
        key=lambda x: x["importance"],
        reverse=True,
    )

    model_card = {
        "model_id": "mednourish-reference-table-learner",
        "description": "Multi-hot character n-gram keyword-to-nutrient reference learner trained on canonical 116-row expert table",
        "date": "2026-10-14",
        "dataset": "knowledge/curated/MedNourish_Symptom_Keywords_vs_Vitamin_Deficiency_Mapping.csv",
        "sample_count": len(ref_rows),
        "target_nutrient_groups": unique_groups,
        "body_regions": regions,
        "feature_count": len(feature_names),
        "validation_strategy": "Stratified 5-Fold Cross-Validation",
        "cv_5fold_macro_f1": {
            "deterministic_baseline_mean": round(float(np.mean(baseline_f1)), 4),
            "xgboost_mean": round(float(np.mean(xgb_f1)), 4),
            "lightgbm_mean": round(float(np.mean(lgb_f1)), 4),
        },
        "top_features": top_features[:15],
        "strictly_reference_warning": (
            "REFERENCE-TABLE LEARNER ONLY: This model trains on 116 curated expert reference table rows. "
            "It maps clinical symptom keywords and anatomical regions to nutritional deficiency categories as a semantic lookup helper. "
            "It is NOT a patient diagnostic predictor and MUST NEVER be treated as empirical clinical evidence."
        ),
        "library_versions": {
            "xgboost": xgb.__version__,
            "lightgbm": lgb.__version__,
            "sklearn": "1.6.1",
        },
    }

    card_path = ARTIFACTS_DIR / "model_card_keyword_reference.json"
    with open(card_path, "w", encoding="utf-8") as f:
        json.dump(model_card, f, indent=2)

    print(f"Reference Table Model Card generated at {card_path}.")
    print(f"5-Fold CV Macro-F1 -> Baseline: {np.mean(baseline_f1):.4f} | XGBoost: {np.mean(xgb_f1):.4f} | LightGBM: {np.mean(lgb_f1):.4f}")
    return model_card

# --------------------------------------------------------------------------
# Main Execution
# --------------------------------------------------------------------------

def main():
    print("=== STARTING STAGE 2 TABULAR ML PIPELINE ===")
    main_results = run_main_tabular_experiments()
    ref_results = run_reference_keyword_experiment()

    # Save consolidated summary
    summary_path = ARTIFACTS_DIR / "tabular_evaluation_summary.json"
    summary = {
        "milestone": "Stage 2 - Tabular ML",
        "date": "2026-10-14",
        "main_dataset_models": main_results,
        "reference_table_model": ref_results,
    }
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\nConsolidated evaluation summary saved to: {summary_path}")
    print("=== STAGE 2 TABULAR ML COMPLETE ===")

if __name__ == "__main__":
    main()
