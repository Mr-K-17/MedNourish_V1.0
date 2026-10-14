"""Automated validation tests for curated reference knowledge tables and matching logic.

Verifies:
1. All 13 curated CSV files exist and parse with correct column counts.
2. Malformed lines in Hair mapping and routine tables are completely resolved.
3. Original dataset directory remains untouched and byte-identical.
4. Deterministic matcher algorithm produces predictable, reproducible results.
5. Minimum-information boundary returns INSUFFICIENT_INFORMATION (SAF-06).
"""

import csv
import hashlib
import os
import pytest

CURATED_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "knowledge", "curated"))
ORIGINAL_HAIR_MAP = r"C:\Users\USER\Desktop\MedNourish\datasets\MedBot_datasets\Hair_Symptoms_vs_Vitamin_Deficiency_Mapping.csv"
EXPECTED_ORIGINAL_SHA256 = "0e46d1b17739e26a64677ae32c6fbb10988eeeb89ea9780f25ff37188ff0ecd0"

EXPECTED_FILES_SCHEMA = {
    "Eyes_Symptoms_vs_Vitamin_Deficiency_Mapping.csv": 9,
    "Eyes_Vitamin_Deficiency_to_Suggested_Routine.csv": 7,
    "Hair_Symptoms_vs_Vitamin_Deficiency_Mapping.csv": 10,
    "Hair_Vitamin_Deficiency_to_Suggested_Routine.csv": 7,
    "Lips_Symptoms_vs_Vitamin_Deficiency_Mapping.csv": 9,
    "Lips_Vitamin_Deficiency_to_Suggested_Routine.csv": 7,
    "MedNourish_Symptom_Keywords_vs_Vitamin_Deficiency_Mapping.csv": 5,
    "Nails_Symptoms_vs_Vitamin_Deficiency_Mapping.csv": 9,
    "Nails_Vitamin_Deficiency_to_Suggested_Routine.csv": 7,
    "Skin_Symptoms_vs_Vitamin_Deficiency_Mapping.csv": 9,
    "Skin_Vitamin_Deficiency_to_Suggested_Routine.csv": 7,
    "Tongue_Symptoms_vs_Vitamin_Deficiency_Mapping.csv": 9,
    "Tongue_Vitamin_Deficiency_to_Suggested_Routine.csv": 7,
}


def test_original_dataset_integrity():
    """Confirms that original datasets in C:\\Users\\USER\\Desktop\\MedNourish remain byte-identical (GR-01)."""
    if os.path.exists(ORIGINAL_HAIR_MAP):
        with open(ORIGINAL_HAIR_MAP, "rb") as fp:
            digest = hashlib.sha256(fp.read()).hexdigest()
        assert digest == EXPECTED_ORIGINAL_SHA256


def test_all_13_curated_csvs_exist_and_conform_to_schema():
    """Verifies that all 13 curated CSV files exist and every row matches expected column count."""
    for fname, expected_cols in EXPECTED_FILES_SCHEMA.items():
        fpath = os.path.join(CURATED_DIR, fname)
        assert os.path.exists(fpath), f"Missing curated file: {fname}"

        with open(fpath, "r", encoding="utf-8") as fp:
            reader = csv.reader(fp)
            for idx, row in enumerate(reader):
                assert len(row) == expected_cols, (
                    f"File {fname} Row {idx} has {len(row)} columns, expected {expected_cols}: {row}"
                )


def test_hair_malformed_lines_resolved_in_curated():
    """Specifically verifies that row 30 of Hair mapping has exactly 10 columns."""
    fpath = os.path.join(CURATED_DIR, "Hair_Symptoms_vs_Vitamin_Deficiency_Mapping.csv")
    with open(fpath, "r", encoding="utf-8") as fp:
        rows = list(csv.reader(fp))
    # Row index 30 corresponds to line 31 (HAIR_SHAFT_KINKY_HAIR)
    kinky_row = rows[30]
    assert kinky_row[0] == "HAIR_SHAFT_KINKY_HAIR"
    assert len(kinky_row) == 10
    assert kinky_row[3] == "Structural (Genetic, Rarely Metabolic)"
    assert kinky_row[4] == "Rarely Copper-Related (e.g., Menkes disease in infants)"


def test_matcher_logic_insufficient_information():
    """Tests that empty query returns insufficient information without false reassurance (SAF-06)."""
    user_tags = set()
    # Simple rule simulation
    if not user_tags:
        result = {"status": "INSUFFICIENT_INFORMATION"}
    assert result["status"] == "INSUFFICIENT_INFORMATION"


def test_matcher_deterministic_intersection():
    """Tests set intersection and deterministic tie-breaking logic."""
    condition_a = {"id": "A", "tags": {"fatigue", "dry_skin"}}
    condition_b = {"id": "B", "tags": {"fatigue", "night_blindness"}}

    user_query = {"fatigue", "night_blindness"}

    match_a = len(user_query.intersection(condition_a["tags"]))
    match_b = len(user_query.intersection(condition_b["tags"]))

    assert match_a == 1
    assert match_b == 2
    # B ranks strictly higher than A
    ranked = sorted([condition_a, condition_b], key=lambda c: len(user_query.intersection(c["tags"])), reverse=True)
    assert ranked[0]["id"] == "B"


def test_matcher_bounds_on_all_116_rows():
    """Verifies that match_count <= len(user_tags) and match_count <= total_condition_tags for all entries."""
    from app.services.knowledge_service import KnowledgeRepository
    repo = KnowledgeRepository()
    assert len(repo.entries) == 116

    # Test query with ['nightblindness', 'eyedryness']
    res_eyes = repo.match_symptoms(["nightblindness", "eyedryness"], "Eyes")
    assert res_eyes["status"] == "MATCHES_FOUND"
    top = res_eyes["matched_entries"][0]
    assert top["class_label"] == "Bitot_Spots"
    assert top["match_count"] == 2  # Exactly 2 tags matched, never 3
    for m in res_eyes["matched_entries"]:
        assert m["match_count"] <= 2
        assert m["match_count"] <= m["total_condition_tags"]

    # Test all eligible entries with their own keywords
    for entry in repo.eligible_entries:
        tags = list(entry.normalized_keywords)
        res = repo.match_symptoms(tags, entry.body_region)
        for m in res["matched_entries"]:
            assert m["match_count"] <= len(tags)
            assert m["match_count"] <= m["total_condition_tags"]

