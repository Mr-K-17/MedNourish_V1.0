"""
MedNourish — Computer Vision Manifests & Image Audit Test Suite
==============================================================
Module: ml.tests.test_image_manifests
Spec: Phase 3.3 Stage 3

Tests:
1. Existence and completeness of docs/IMAGE_DATA_REPORT.md.
2. Presence and validity of class map YAML specifications in ml/class_maps/.
3. Manifest generation, valid columns, non-empty splits (train/val/test).
4. Deduplication verification (zero SHA256 exact duplicates within manifests).
5. Split ratio checks (~70% train, ~15% val, ~15% test).
"""

import csv
import sys
from pathlib import Path
import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

CLASS_MAPS_DIR = Path("ml/class_maps")
MANIFESTS_DIR = Path("ml/artifacts/manifests")
DOCS_DIR = Path("docs")

def test_image_data_report_exists_and_complete():
    report_path = DOCS_DIR / "IMAGE_DATA_REPORT.md"
    assert report_path.exists(), "docs/IMAGE_DATA_REPORT.md must exist"
    content = report_path.read_text(encoding="utf-8")
    for model_name in ["combined", "eyes", "hair", "lips", "nails", "skin", "tongue"]:
        assert model_name.upper() in content, f"Model {model_name} must be featured in report"
    assert "Executive Summary Table" in content
    assert "Known Methodological Risks" in content
    assert "Source-per-Class Shortcut Learning" in content

def test_class_map_yamls():
    models = ["combined", "eyes", "hair", "lips", "nails", "skin", "tongue"]
    for m in models:
        y_path = CLASS_MAPS_DIR / f"{m}.yaml"
        assert y_path.exists(), f"Class map YAML missing: {y_path}"
        with open(y_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            assert data["model"] == m
            assert "classes" in data
            assert "dataset_root" in data

def test_manifest_schema_and_deduplication():
    # Test available manifests
    manifest_files = list(MANIFESTS_DIR.glob("*_manifest.csv"))
    assert len(manifest_files) >= 5, f"Expected at least 5 generated manifests, found {len(manifest_files)}"

    for mf in manifest_files:
        with open(mf, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        if not rows:
            continue

        # Verify required headers
        required_cols = {
            "filepath", "relative_path", "class_name", "split",
            "sha256", "phash", "width", "height",
            "blur_variance", "mean_luminance", "quality_pass"
        }
        assert required_cols.issubset(set(rows[0].keys())), f"Missing headers in {mf.name}"

        # Verify zero exact duplicates by sha256
        hashes = [r["sha256"] for r in rows]
        assert len(hashes) == len(set(hashes)), f"Exact duplicates found in {mf.name}"

        # Verify splits
        splits = {r["split"] for r in rows}
        assert "train" in splits, f"Missing train split in {mf.name}"
        assert "val" in splits, f"Missing val split in {mf.name}"
        assert "test" in splits, f"Missing test split in {mf.name}"

        # Verify split proportions (approx 70 / 15 / 15)
        train_count = sum(1 for r in rows if r["split"] == "train")
        val_count = sum(1 for r in rows if r["split"] == "val")
        test_count = sum(1 for r in rows if r["split"] == "test")
        total = len(rows)

        assert 0.55 <= (train_count / total) <= 0.85, f"Train proportion out of expected range in {mf.name}"
        assert 0.08 <= (val_count / total) <= 0.25, f"Val proportion out of expected range in {mf.name}"
        assert 0.08 <= (test_count / total) <= 0.25, f"Test proportion out of expected range in {mf.name}"
