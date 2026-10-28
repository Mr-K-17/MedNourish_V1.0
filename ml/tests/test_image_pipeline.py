"""
Unit tests for MedNourish OpenCV Image Pipeline and MobileNetV2 Workflow
========================================================================
Test module: ml.tests.test_image_pipeline
Spec: docs/CV_PIPELINE_SPEC.md
"""

import os
import shutil
import tempfile
import cv2
import numpy as np
import pytest

from ml.image_pipeline import (
    QualityConfig,
    ImageInspectionResult,
    load_image_rgb,
    calculate_blur_variance,
    calculate_mean_luminance,
    resize_with_pad,
    rescale_mobilenetv2_input,
    inspect_and_preprocess_image,
    build_image_manifest,
)
from ml.mobilenet_workflow import (
    MobileNetV2Hyperparameters,
    MobileNetV2Pipeline,
    audit_corpus_labels,
    generate_tflite_conversion_specification,
)


@pytest.fixture
def temp_test_dir():
    """Provides a temporary directory for synthetic image fixtures."""
    d = tempfile.mkdtemp(prefix="mednourish_cv_test_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


def create_synthetic_image(
    path: str,
    width: int = 120,
    height: int = 100,
    color: tuple = (128, 128, 128),
    add_texture: bool = True
) -> str:
    """Helper to create a synthetic image on disk."""
    img = np.full((height, width, 3), color, dtype=np.uint8)
    if add_texture:
        # Add high-frequency checkerboard / lines so Laplacian variance > 100
        cv2.line(img, (0, 0), (width, height), (255, 255, 255), 2)
        cv2.circle(img, (width // 2, height // 2), 20, (0, 0, 0), -1)
        for i in range(0, width, 10):
            cv2.line(img, (i, 0), (i, height), (50, 200, 50), 1)
    cv2.imwrite(path, img)
    return path


# --- 1. Safe Image Loading & Corrupt File Handling ---

def test_load_image_rgb_valid(temp_test_dir):
    p = os.path.join(temp_test_dir, "valid.png")
    create_synthetic_image(p, 100, 100, (50, 100, 150))
    rgb = load_image_rgb(p)
    assert rgb is not None
    assert rgb.shape == (100, 100, 3)
    assert rgb.dtype == np.uint8


def test_load_image_rgb_corrupt_file(temp_test_dir):
    p = os.path.join(temp_test_dir, "corrupt.jpg")
    with open(p, "wb") as f:
        f.write(b"NOT_AN_IMAGE_HEADER_CORRUPT_BYTES")
    rgb = load_image_rgb(p)
    assert rgb is None


def test_load_image_rgb_nonexistent_file():
    rgb = load_image_rgb("nonexistent/path/image.jpg")
    assert rgb is None


# --- 2. Color Space and Letterbox Resizing ---

def test_resize_with_pad_aspect_ratio_preservation():
    # Anisotropic input: 100 tall, 200 wide
    img = np.full((100, 200, 3), 200, dtype=np.uint8)
    padded = resize_with_pad(img, target_size=(224, 224))
    assert padded.shape == (224, 224, 3)
    assert padded.dtype == np.uint8

    # Check top/bottom letterbox padding (black bars: pad_color=(0,0,0))
    # Scaled height = 224 * (100 / 200) = 112
    # Padding top = (224 - 112) // 2 = 56
    assert np.all(padded[0, :, :] == 0)
    assert np.all(padded[55, :, :] == 0)
    # Center should contain the image content (200)
    assert np.all(padded[112, 100, :] == 200)


def test_rescale_mobilenetv2_input():
    img = np.array([[[0, 128, 255]]], dtype=np.uint8)
    rescaled = rescale_mobilenetv2_input(img)
    assert rescaled.dtype == np.float32
    assert pytest.approx(rescaled[0, 0, 0], abs=0.01) == -1.0
    assert pytest.approx(rescaled[0, 0, 1], abs=0.02) == 0.0
    assert pytest.approx(rescaled[0, 0, 2], abs=0.01) == 1.0


# --- 3. Diagnostics & Quality Thresholds ---

def test_quality_check_dimension_outlier(temp_test_dir):
    p = os.path.join(temp_test_dir, "tiny.png")
    create_synthetic_image(p, width=32, height=32, add_texture=False)
    res = inspect_and_preprocess_image(p, config=QualityConfig(min_dimension=64))
    assert not res.is_valid
    assert res.status == "EXCLUDED_DIMENSION_OUTLIER"


def test_quality_check_blur_detection(temp_test_dir):
    p = os.path.join(temp_test_dir, "flat_blur.png")
    # Completely flat color has 0 Laplacian variance
    create_synthetic_image(p, width=128, height=128, color=(100, 100, 100), add_texture=False)
    res = inspect_and_preprocess_image(p, config=QualityConfig(blur_threshold=100.0))
    assert not res.is_valid
    assert res.status == "EXCLUDED_BLUR_THRESHOLD"


def test_quality_check_underexposure(temp_test_dir):
    p = os.path.join(temp_test_dir, "dark.png")
    create_synthetic_image(p, width=128, height=128, color=(10, 10, 10), add_texture=False)
    res = inspect_and_preprocess_image(p, config=QualityConfig(blur_threshold=0.0, min_luminance=30.0))
    assert not res.is_valid
    assert res.status == "EXCLUDED_UNDEREXPOSURE"


def test_quality_check_overexposure(temp_test_dir):
    p = os.path.join(temp_test_dir, "bright.png")
    create_synthetic_image(p, width=128, height=128, color=(240, 240, 240), add_texture=False)
    res = inspect_and_preprocess_image(p, config=QualityConfig(blur_threshold=0.0, max_luminance=225.0))
    assert not res.is_valid
    assert res.status == "EXCLUDED_OVEREXPOSURE"


def test_quality_check_passed(temp_test_dir):
    p = os.path.join(temp_test_dir, "good.png")
    create_synthetic_image(p, width=150, height=150, color=(120, 120, 120), add_texture=True)
    res = inspect_and_preprocess_image(p, config=QualityConfig(blur_threshold=50.0))
    assert res.is_valid
    assert res.status == "PASSED"
    assert res.processed_shape == (224, 224, 3)
    assert res.pixel_min is not None and res.pixel_min >= -1.0
    assert res.pixel_max is not None and res.pixel_max <= 1.0


# --- 4. Manifest Generation ---

def test_build_image_manifest(temp_test_dir):
    good_p = os.path.join(temp_test_dir, "manifest_good.png")
    create_synthetic_image(good_p, 150, 150, (120, 120, 120), add_texture=True)

    bad_p = os.path.join(temp_test_dir, "manifest_bad.png")
    create_synthetic_image(bad_p, 30, 30, (120, 120, 120), add_texture=False)

    manifest_file = os.path.join(temp_test_dir, "manifest.json")
    manifest = build_image_manifest(
        [good_p, bad_p],
        config=QualityConfig(blur_threshold=50.0),
        output_manifest_path=manifest_file
    )

    assert manifest["total_evaluated"] == 2
    assert manifest["passed_count"] == 1
    assert manifest["excluded_count"] == 1
    assert os.path.isfile(manifest_file)


# --- 5. MobileNetV2 Pipeline & Audit Findings ---

def test_audit_corpus_labels():
    findings = audit_corpus_labels("datasets/")
    assert not findings.patient_session_identifiers_present
    assert not findings.label_mapping_valid_for_clinical_training
    assert "public vision archives" in findings.corpus_provenance


def test_mobilenetv2_pipeline_smoke_test():
    pipeline = MobileNetV2Pipeline(MobileNetV2Hyperparameters(input_shape=(224, 224, 3)))
    pipeline.set_classes(["Normal", "Bitot_Spots", "Conjunctival_Xerosis", "Koilonychia"])
    report = pipeline.run_smoke_test(samples_per_class=4)

    assert report["status"] == "SMOKE_TEST_PASSED"
    assert report["pipeline_integrity_verified"] is True
    assert report["input_tensor_shape"] == [11, 224, 224, 3]  # 70% of 16 = 11
    assert report["target_tensor_shape"] == [11, 4]


def test_tflite_conversion_specification():
    spec = generate_tflite_conversion_specification()
    assert "float32_tflite" in spec["conversion_targets"]
    assert spec["parity_verification_gate"]["top1_categorical_agreement_threshold"] == 0.995
