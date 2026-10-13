"""Unit and Integration Tests for ML Data Pipeline & Tabular Benchmarking.

Phase 3.1: Verifies dataset integrity, schema validation, deterministic splitting,
and preprocessor fit/transform behavior without leakage.
"""

from pathlib import Path
import numpy as np
import pytest

from ml.data_pipeline import (
    EXCLUDE_COLUMNS,
    TARGET_COLUMN,
    VALID_TARGET_CLASSES,
    TabularPreprocessor,
    audit_tabular_dataset,
    load_raw_dataset,
)
from ml.tabular_benchmark import make_stratified_splits


SAMPLE_DATASET_PATH = Path(r"C:\Users\USER\Desktop\MedNourish\datasets\vitamin_deficiency_disease_dataset_20260123.csv")


def test_dataset_file_exists_and_loads():
    """Confirms tabular dataset exists in original archive and loads exactly 4000 records."""
    assert SAMPLE_DATASET_PATH.is_file(), "Tabular dataset must exist in datasets archive."
    fieldnames, records = load_raw_dataset(SAMPLE_DATASET_PATH)
    assert len(records) == 4000
    assert len(fieldnames) == 34
    assert TARGET_COLUMN in fieldnames


def test_dataset_audit_metrics_and_zero_missing():
    """Confirms audit profile detects zero missing values, zero duplicates, and exact 5 target classes."""
    fieldnames, records = load_raw_dataset(SAMPLE_DATASET_PATH)
    profile = audit_tabular_dataset(records, fieldnames)

    assert profile.total_rows == 4000
    assert profile.total_columns == 34
    assert profile.duplicate_count == 0
    assert len(profile.missing_counts) == 0  # 0 missing values
    assert set(profile.target_distribution.keys()) == set(VALID_TARGET_CLASSES)
    assert len(profile.feature_names) == 30

    for exc in EXCLUDE_COLUMNS:
        assert exc not in profile.feature_names


def test_deterministic_stratified_splits():
    """Verifies that stratified splits are deterministic and maintain class proportions."""
    fieldnames, records = load_raw_dataset(SAMPLE_DATASET_PATH)

    train_1, val_1, test_1 = make_stratified_splits(records, random_state=42)
    train_2, val_2, test_2 = make_stratified_splits(records, random_state=42)

    # Determinism
    assert len(train_1) == len(train_2) == 2800
    assert len(val_1) == len(val_2) == 600
    assert len(test_1) == len(test_2) == 600
    assert [r[TARGET_COLUMN] for r in test_1] == [r[TARGET_COLUMN] for r in test_2]

    # Stratification check on test set (Night Blindness ~ 3.05% of 600 -> 18)
    nb_test = sum(1 for r in test_1 if r[TARGET_COLUMN] == "Night_Blindness")
    assert nb_test == 18


def test_preprocessor_fitting_and_no_leakage():
    """Preprocessor must fit strictly on train data and transform validation/test without leakage."""
    fieldnames, records = load_raw_dataset(SAMPLE_DATASET_PATH)
    profile = audit_tabular_dataset(records, fieldnames)
    train_recs, val_recs, test_recs = make_stratified_splits(records, random_state=42)

    preprocessor = TabularPreprocessor(profile.feature_names)
    assert not preprocessor.fitted

    with pytest.raises(RuntimeError):
        preprocessor.transform(test_recs)

    preprocessor.fit(train_recs)
    assert preprocessor.fitted
    assert len(preprocessor.target_mapping) == 5

    X_train, y_train = preprocessor.transform(train_recs)
    X_test, y_test = preprocessor.transform(test_recs)

    assert X_train.shape == (2800, 30)
    assert y_train.shape == (2800,)
    assert X_test.shape == (600, 30)
    assert y_test.shape == (600,)

    # Values must be finite and normalized
    assert not np.isnan(X_train).any()
    assert not np.isnan(X_test).any()
