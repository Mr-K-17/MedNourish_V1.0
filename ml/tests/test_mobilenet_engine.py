"""
Automated Unit Tests for MobileNetV2 Architecture & Edge Export Engine
======================================================================
Test module: ml.tests.test_mobilenet_engine
Spec: docs/CV_PIPELINE_SPEC.md & Phase 3.3 Proof of Pipeline
"""

import os
import shutil
import tempfile
import numpy as np
import onnx
import onnxruntime as ort
import pytest

from ml.image_pipeline import QualityConfig, resize_with_pad, rescale_mobilenetv2_input
from ml.mobilenet_engine import ArchitectureConfig, MobileNetV2Classifier


@pytest.fixture
def temp_output_dir():
    d = tempfile.mkdtemp(prefix="mednourish_mobilenet_test_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


# --- 1. Model Construction & Forward Pass Shapes ---

def test_mobilenetv2_initialization():
    config = ArchitectureConfig(num_classes=5, feature_dim=1280)
    model = MobileNetV2Classifier(config)
    assert model.W.shape == (1280, 5)
    assert model.b.shape == (5,)
    assert model.W.dtype == np.float32


def test_mobilenetv2_forward_features():
    model = MobileNetV2Classifier(ArchitectureConfig(num_classes=4))
    # 2 sample images with shape (224, 224, 3)
    x = np.random.uniform(-1.0, 1.0, size=(2, 224, 224, 3)).astype(np.float32)
    features = model.forward_features(x)
    assert features.shape == (2, 1280)
    assert np.all(features >= 0.0)  # ReLU6 non-negativity


def test_mobilenetv2_predict_proba_and_classes():
    model = MobileNetV2Classifier(ArchitectureConfig(num_classes=4))
    x = np.random.uniform(-1.0, 1.0, size=(3, 224, 224, 3)).astype(np.float32)
    probs = model.predict_proba(x)
    assert probs.shape == (3, 4)
    # Probability axiom: sums to 1.0 across classes
    assert np.allclose(np.sum(probs, axis=1), 1.0, atol=1e-5)

    preds = model.predict(x)
    assert preds.shape == (3,)
    assert all(0 <= p < 4 for p in preds)


def test_mobilenetv2_invalid_input_shape_rejection():
    model = MobileNetV2Classifier()
    invalid_x = np.random.randn(2, 100, 100, 3).astype(np.float32)
    with pytest.raises(ValueError, match="Input tensor shape mismatch"):
        model.forward_features(invalid_x)


# --- 2. Minimal Training Step & Loss Verification ---

def test_mobilenetv2_train_step_loss_reduction():
    model = MobileNetV2Classifier(ArchitectureConfig(learning_rate=0.5, label_smoothing=0.0))
    x = np.random.uniform(-1.0, 1.0, size=(8, 224, 224, 3)).astype(np.float32)
    y = np.random.randint(0, 4, size=8)

    step_result = model.train_step(x, y)
    assert "initial_loss" in step_result
    assert "updated_loss" in step_result
    # Training step must decrease cross-entropy loss on the batch
    assert step_result["updated_loss"] <= step_result["initial_loss"]


# --- 3. ONNX Model Export & Inference Execution ---

def test_mobilenetv2_onnx_export_and_runtime_inference(temp_output_dir):
    model = MobileNetV2Classifier(ArchitectureConfig(num_classes=4))
    onnx_file = os.path.join(temp_output_dir, "mobilenetv2_test.onnx")

    exported_path = model.export_onnx(onnx_file)
    assert os.path.isfile(exported_path)
    assert os.path.getsize(exported_path) > 0

    # Load with ONNX Runtime
    session = ort.InferenceSession(exported_path)
    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name

    assert input_name == "input"
    assert output_name == "output"

    # Run inference with shape (1, 3, 224, 224)
    dummy_input = np.random.uniform(-1.0, 1.0, size=(1, 3, 224, 224)).astype(np.float32)
    onnx_out = session.run([output_name], {input_name: dummy_input})[0]

    assert onnx_out.shape == (1, 4)
    assert np.isclose(np.sum(onnx_out), 1.0, atol=1e-5)


# --- 4. Quantization Parity Verification ---

def test_mobilenetv2_quantization_parity():
    model = MobileNetV2Classifier(ArchitectureConfig(num_classes=4))
    test_inputs = np.random.uniform(-1.0, 1.0, size=(20, 224, 224, 3)).astype(np.float32)

    parity = model.evaluate_quantization_parity(test_inputs, max_discrepancy_threshold=0.15)
    assert parity["test_samples"] == 20
    assert parity["max_probability_discrepancy"] <= 0.15
    assert parity["top1_class_agreement"] >= 0.90
    assert parity["parity_gate_passed"] is True


# --- 5. End-to-End OpenCV Preprocessing Integration ---

def test_opencv_preprocessing_to_mobilenet_inference():
    # Synthetic raw BGR image 150x200
    raw_bgr = np.full((150, 200, 3), 120, dtype=np.uint8)
    # Preprocess via OpenCV
    padded_rgb = resize_with_pad(raw_bgr, target_size=(224, 224))
    scaled_input = rescale_mobilenetv2_input(padded_rgb)

    assert scaled_input.shape == (224, 224, 3)
    assert scaled_input.dtype == np.float32
    assert -1.0 <= scaled_input.min() <= 1.0

    # Feedforward into model
    model = MobileNetV2Classifier(ArchitectureConfig(num_classes=3))
    probs = model.predict_proba(scaled_input)
    assert probs.shape == (1, 3)
    assert np.isclose(np.sum(probs), 1.0, atol=1e-5)
