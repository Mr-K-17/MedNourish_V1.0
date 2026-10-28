"""Reproducible Training & Evaluation Pipeline for Tabular Models.

Phase 3.1: Stratified train/val/test splitting, baseline dummy model,
XGBoost, and LightGBM comparison on held-out test data.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    f1_score,
    log_loss,
)
from sklearn.model_selection import train_test_split
import xgboost as xgb
import lightgbm as lgb

from ml.data_pipeline import (
    TabularPreprocessor,
    audit_tabular_dataset,
    load_raw_dataset,
)


RANDOM_SEED = 42


def make_stratified_splits(
    records: List[Dict[str, str]],
    target_col: str = "disease_diagnosis",
    test_size: float = 0.15,
    val_size: float = 0.15,
    random_state: int = RANDOM_SEED,
) -> Tuple[List[Dict[str, str]], List[Dict[str, str]], List[Dict[str, str]]]:
    """Generates deterministic, stratified train / validation / test splits."""
    labels = [r[target_col] for r in records]

    # First split off held-out test set
    train_val_records, test_records, train_val_labels, _ = train_test_split(
        records,
        labels,
        test_size=test_size,
        stratify=labels,
        random_state=random_state,
    )

    # Relative val size of remaining train_val
    adjusted_val_size = val_size / (1.0 - test_size)
    train_records, val_records, _, _ = train_test_split(
        train_val_records,
        train_val_labels,
        test_size=adjusted_val_size,
        stratify=train_val_labels,
        random_state=random_state,
    )

    return train_records, val_records, test_records


def evaluate_model_predictions(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray,
    target_names: List[str],
) -> Dict[str, Any]:
    """Computes held-out multi-class metrics including macro/weighted F1 and balanced accuracy."""
    acc = float(accuracy_score(y_true, y_pred))
    bal_acc = float(balanced_accuracy_score(y_true, y_pred))
    f1_macro = float(f1_score(y_true, y_pred, average="macro"))
    f1_weighted = float(f1_score(y_true, y_pred, average="weighted"))
    loss = float(log_loss(y_true, y_prob))

    cls_report = classification_report(
        y_true,
        y_pred,
        target_names=target_names,
        output_dict=True,
        zero_division=0,
    )

    return {
        "accuracy": round(acc, 4),
        "balanced_accuracy": round(bal_acc, 4),
        "macro_f1": round(f1_macro, 4),
        "weighted_f1": round(f1_weighted, 4),
        "log_loss": round(loss, 4),
        "classification_report": cls_report,
    }


def run_tabular_experiment(
    csv_path: Path, output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """Executes full reproducible benchmark training and evaluation."""
    fieldnames, records = load_raw_dataset(csv_path)
    profile = audit_tabular_dataset(records, fieldnames)

    # 1. Stratified split (70% train, 15% val, 15% test)
    train_recs, val_recs, test_recs = make_stratified_splits(
        records, test_size=0.15, val_size=0.15, random_state=RANDOM_SEED
    )

    # 2. Fit preprocessor strictly on train split
    preprocessor = TabularPreprocessor(profile.feature_names)
    preprocessor.fit(train_recs)

    X_train, y_train = preprocessor.transform(train_recs)
    X_val, y_val = preprocessor.transform(val_recs)
    X_test, y_test = preprocessor.transform(test_recs)

    target_names = [preprocessor.target_inverse_mapping[i] for i in range(len(preprocessor.target_mapping))]

    # 3. Baseline: Most Frequent Dummy Classifier
    dummy = DummyClassifier(strategy="most_frequent", random_state=RANDOM_SEED)
    dummy.fit(X_train, y_train)
    dummy_pred = dummy.predict(X_test)
    dummy_prob = dummy.predict_proba(X_test)
    dummy_metrics = evaluate_model_predictions(y_test, dummy_pred, dummy_prob, target_names)

    # 4. Candidate A: XGBoost Classifier
    xgb_model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="multi:softprob",
        random_state=RANDOM_SEED,
        eval_metric="mlogloss",
    )
    xgb_model.fit(
        X_train,
        y_train,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )
    xgb_pred = xgb_model.predict(X_test)
    xgb_prob = xgb_model.predict_proba(X_test)
    xgb_metrics = evaluate_model_predictions(y_test, xgb_pred, xgb_prob, target_names)

    # 5. Candidate B: LightGBM Classifier
    lgb_model = lgb.LGBMClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="multiclass",
        random_state=RANDOM_SEED,
        verbosity=-1,
    )
    lgb_model.fit(
        X_train,
        y_train,
        eval_set=[(X_val, y_val)],
    )
    lgb_pred = lgb_model.predict(X_test)
    lgb_prob = lgb_model.predict_proba(X_test)
    lgb_metrics = evaluate_model_predictions(y_test, lgb_pred, lgb_prob, target_names)

    results: Dict[str, Any] = {
        "dataset_profile": {
            "total_rows": profile.total_rows,
            "feature_count": len(profile.feature_names),
            "features": profile.feature_names,
            "target_classes": target_names,
            "target_distribution": profile.target_distribution,
        },
        "split_counts": {
            "train": len(train_recs),
            "val": len(val_recs),
            "test": len(test_recs),
        },
        "benchmarks": {
            "dummy_baseline": dummy_metrics,
            "xgboost": xgb_metrics,
            "lightgbm": lgb_metrics,
        },
        "top_features_xgboost": [
            {"feature": feat, "importance": round(float(imp), 4)}
            for feat, imp in sorted(
                zip(profile.feature_names, xgb_model.feature_importances_),
                key=lambda x: -x[1],
            )[:10]
        ],
    }

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        report_file = output_dir / "tabular_benchmark_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

    return results


if __name__ == "__main__":
    archive_csv = Path(r"C:\Users\USER\Desktop\MedNourish\datasets\vitamin_deficiency_disease_dataset_20260123.csv")
    out_dir = Path(__file__).resolve().parent / "artifacts"
    res = run_tabular_experiment(archive_csv, out_dir)
    print("Tabular benchmark complete!")
    print(f"XGBoost Test Accuracy: {res['benchmarks']['xgboost']['accuracy']}, Macro F1: {res['benchmarks']['xgboost']['macro_f1']}")
    print(f"LightGBM Test Accuracy: {res['benchmarks']['lightgbm']['accuracy']}, Macro F1: {res['benchmarks']['lightgbm']['macro_f1']}")
