"""
MedNourish — MobileNetV2 Keras & TFLite Test Suite
=================================================
Module: ml.tests.test_mobilenet_keras
Spec: Phase 3.3 Stage 4

Tests:
1. Architecture initialization and synthetic smoke test verification.
2. TFLite model artifact generation (Float32 and DRQ quantized).
3. TFLite numerical parity gate (max-diff < 0.01, top-1 agreement >= 99.5%).
4. Grad-CAM sample visual overlays.
5. Completeness of docs/ML_RESULTS.md.
"""

import json
import sys
from pathlib import Path
import pytest
import numpy as np
import tensorflow as tf

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ml.mobilenet_keras import build_mobilenetv2_classifier, run_synthetic_smoke_tests

VISION_ARTIFACTS_DIR = Path("ml/artifacts/vision")
DOCS_DIR = Path("docs")

def test_synthetic_smoke_fixtures():
    smoke_results = run_synthetic_smoke_tests()
    assert smoke_results["forward_shape"] == [4, 5]
    assert smoke_results["loss_decreased"] is True
    assert smoke_results["held_out_batch_shape"] == [2, 5]

def test_vision_artifacts_and_model_cards():
    model_cards = list(VISION_ARTIFACTS_DIR.glob("model_card_*.json"))
    assert len(model_cards) >= 3, f"Expected at least 3 vision model cards, found {len(model_cards)}"

    for mc in model_cards:
        data = json.loads(mc.read_text(encoding="utf-8"))
        m_id = data["model_id"]
        assert "MobileNetV2" in data["architecture"]
        assert data["input_shape"] == [224, 224, 3]
        assert "tflite_verification" in data
        assert "source_shortcut_check" in data
        assert "ACADEMIC DEMO SCOPE ONLY" in data["academic_disclaimer"]

def test_tflite_parity_gates():
    model_cards = list(VISION_ARTIFACTS_DIR.glob("model_card_*.json"))
    for mc in model_cards:
        data = json.loads(mc.read_text(encoding="utf-8"))
        tf_stat = data["tflite_verification"]
        
        # Float32 TFLite Gate
        assert tf_stat["parity_gate_passed"] is True, f"TFLite gate missed for {data['model_id']}"
        assert tf_stat["max_abs_difference"] < 0.01, f"Max diff too high: {tf_stat['max_abs_difference']}"
        assert tf_stat["top1_agreement_pct"] >= 99.5, f"Top-1 agreement below 99.5%: {tf_stat['top1_agreement_pct']}"

        # Real TFLite file exists
        tflite_file = VISION_ARTIFACTS_DIR / tf_stat["tflite_filename"]
        assert tflite_file.exists(), f"TFLite binary missing: {tflite_file}"

        # Dynamic Range Quantization file exists
        drq_stat = tf_stat.get("dynamic_range_quantization", {})
        drq_file = VISION_ARTIFACTS_DIR / drq_stat["tflite_filename"]
        assert drq_file.exists(), f"DRQ TFLite missing: {drq_file}"
        assert drq_stat["top1_agreement_pct"] >= 90.0

def test_gradcam_overlays_generated():
    gradcam_files = list((VISION_ARTIFACTS_DIR / "gradcam").glob("*.png"))
    assert len(gradcam_files) >= 3, "Expected at least 3 Grad-CAM visual overlays"

def test_ml_results_doc_integrity():
    ml_doc = DOCS_DIR / "ML_RESULTS.md"
    assert ml_doc.exists(), "docs/ML_RESULTS.md must exist"
    content = ml_doc.read_text(encoding="utf-8")
    assert "Tabular Model Benchmarks" in content
    assert "Leakage Confirmed" in content
    assert "Realistic Pre-Test Model" in content
    assert "Reference-Table Learner" in content
    assert "MobileNetV2" in content
    assert "TFLite Float32 Gate" in content
