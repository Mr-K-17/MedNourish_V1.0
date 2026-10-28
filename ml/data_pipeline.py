"""Tabular Dataset Audit and Preprocessing Utilities.

Phase 3.1: Data ingestion, schema validation, and leakage-resistant preprocessing
for the tabular vitamin deficiency disease dataset.
"""

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np


TARGET_COLUMN = "disease_diagnosis"

# The 5 ground truth clinical condition classes in the tabular dataset
VALID_TARGET_CLASSES = [
    "Healthy",
    "Anemia",
    "Rickets_Osteomalacia",
    "Night_Blindness",
    "Scurvy",
]

# Categorical features in tabular dataset
CATEGORICAL_FEATURES = [
    "gender",
    "smoking_status",
    "alcohol_consumption",
    "exercise_level",
    "diet_type",
    "sun_exposure",
    "income_level",
    "latitude_region",
]

# Clinical laboratory features (serum & blood levels)
LAB_FEATURES = [
    "hemoglobin_g_dl",
    "serum_vitamin_d_ng_ml",
    "serum_vitamin_b12_pg_ml",
    "serum_folate_ng_ml",
]

# Dietary RDA intake percentage estimates
DIETARY_RDA_FEATURES = [
    "vitamin_a_percent_rda",
    "vitamin_c_percent_rda",
    "vitamin_d_percent_rda",
    "vitamin_e_percent_rda",
    "vitamin_b12_percent_rda",
    "folate_percent_rda",
    "calcium_percent_rda",
    "iron_percent_rda",
]

# Demographic & physical features
DEMOGRAPHIC_FEATURES = [
    "age",
    "bmi",
]

# Binary symptom indicators
SYMPTOM_INDICATORS = [
    "has_night_blindness",
    "has_fatigue",
    "has_bleeding_gums",
    "has_bone_pain",
    "has_muscle_weakness",
    "has_numbness_tingling",
    "has_memory_problems",
    "has_pale_skin",
]

# Feature columns to exclude from training to prevent label leakage:
# - disease_diagnosis: target
# - has_multiple_deficiencies: composite target / label leakage derivative
# - symptoms_list: free-text comma list redundant with binary indicators
# - symptoms_count: redundant aggregate count
EXCLUDE_COLUMNS = [
    "disease_diagnosis",
    "has_multiple_deficiencies",
    "symptoms_list",
    "symptoms_count",
]


@dataclass
class DatasetProfile:
    total_rows: int
    total_columns: int
    feature_names: List[str]
    target_distribution: Dict[str, int]
    missing_counts: Dict[str, int]
    duplicate_count: int


def load_raw_dataset(csv_path: Path) -> Tuple[List[str], List[Dict[str, str]]]:
    """Loads CSV dataset safely into header and list of record dicts."""
    if not csv_path.is_file():
        raise FileNotFoundError(f"Dataset not found at {csv_path}")

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        records = list(reader)
        fieldnames = reader.fieldnames or []

    return fieldnames, records


def audit_tabular_dataset(records: List[Dict[str, str]], fieldnames: List[str]) -> DatasetProfile:
    """Computes comprehensive summary profile and validation checks."""
    total_rows = len(records)
    total_columns = len(fieldnames)

    missing_counts: Dict[str, int] = {fn: 0 for fn in fieldnames}
    target_dist: Dict[str, int] = {}
    row_signatures = set()
    dup_count = 0

    for r in records:
        sig = tuple(r.get(fn, "") for fn in fieldnames)
        if sig in row_signatures:
            dup_count += 1
        else:
            row_signatures.add(sig)

        for fn in fieldnames:
            val = r.get(fn, "")
            if val is None or val.strip() == "":
                missing_counts[fn] += 1

        tgt = r.get(TARGET_COLUMN, "")
        target_dist[tgt] = target_dist.get(tgt, 0) + 1

    feature_names = [fn for fn in fieldnames if fn not in EXCLUDE_COLUMNS]

    return DatasetProfile(
        total_rows=total_rows,
        total_columns=total_columns,
        feature_names=feature_names,
        target_distribution=target_dist,
        missing_counts={k: v for k, v in missing_counts.items() if v > 0},
        duplicate_count=dup_count,
    )


class TabularPreprocessor:
    """Reproducible encoder and standardizer for tabular records.

    Fits transformations STRICTLY on training split; transforms test/validation
    splits without information leakage.
    """

    def __init__(self, feature_names: List[str], target_name: str = TARGET_COLUMN):
        self.feature_names = feature_names
        self.target_name = target_name
        self.cat_mappings: Dict[str, Dict[str, int]] = {}
        self.target_mapping: Dict[str, int] = {}
        self.target_inverse_mapping: Dict[int, str] = {}
        self.numeric_means: Dict[str, float] = {}
        self.numeric_stds: Dict[str, float] = {}
        self.fitted = False

    def fit(self, records: List[Dict[str, str]]) -> "TabularPreprocessor":
        """Fits categorical levels, label encoders, and feature scalers on training split."""
        # 1. Target mapping (deterministic alphabetical order)
        all_targets = sorted(list({r[self.target_name] for r in records}))
        self.target_mapping = {t: idx for idx, t in enumerate(all_targets)}
        self.target_inverse_mapping = {idx: t for t, idx in self.target_mapping.items()}

        # 2. Categorical encoders
        for cat_col in CATEGORICAL_FEATURES:
            if cat_col in self.feature_names:
                unique_vals = sorted(list({r.get(cat_col, "Unknown") for r in records}))
                # Reserve 0 for unknown
                self.cat_mappings[cat_col] = {val: idx for idx, val in enumerate(unique_vals)}

        # 3. Numeric standardizers
        numeric_cols = (
            DEMOGRAPHIC_FEATURES + LAB_FEATURES + DIETARY_RDA_FEATURES + SYMPTOM_INDICATORS
        )
        for num_col in numeric_cols:
            if num_col in self.feature_names:
                vals = [float(r[num_col]) for r in records if r.get(num_col, "").strip()]
                if vals:
                    mean = float(np.mean(vals))
                    std = float(np.std(vals))
                    self.numeric_means[num_col] = mean
                    self.numeric_stds[num_col] = std if std > 1e-7 else 1.0

        self.fitted = True
        return self

    def transform(self, records: List[Dict[str, str]]) -> Tuple[np.ndarray, np.ndarray]:
        """Transforms records into numerical design matrix X and label vector y."""
        if not self.fitted:
            raise RuntimeError("Preprocessor must be fitted on training data before transform.")

        num_samples = len(records)
        num_features = len(self.feature_names)

        X = np.zeros((num_samples, num_features), dtype=np.float32)
        y = np.zeros(num_samples, dtype=np.int64)

        for i, r in enumerate(records):
            for j, fn in enumerate(self.feature_names):
                raw_val = r.get(fn, "")
                if fn in self.cat_mappings:
                    # One-based encoding or index
                    mapping = self.cat_mappings[fn]
                    X[i, j] = float(mapping.get(raw_val, -1))
                else:
                    # Numeric
                    try:
                        fval = float(raw_val)
                    except ValueError:
                        fval = self.numeric_means.get(fn, 0.0)
                    mean = self.numeric_means.get(fn, 0.0)
                    std = self.numeric_stds.get(fn, 1.0)
                    X[i, j] = (fval - mean) / std

            tgt_val = r.get(self.target_name, "")
            y[i] = self.target_mapping.get(tgt_val, -1)

        return X, y
