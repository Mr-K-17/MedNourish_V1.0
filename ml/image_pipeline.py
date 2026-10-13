"""
MedNourish — OpenCV Image Processing and Preprocessing Pipeline
===============================================================
Module: ml.image_pipeline
Spec: docs/CV_PIPELINE_SPEC.md

Provides maintainable, safe image loading, corrupt-file handling,
RGB conversion, aspect-ratio-preserving letterbox resizing, quality
diagnostics (blur, luminance, dimension thresholds), and reproducible
manifest generation with explicit exclusion audit logging.
"""

from __future__ import annotations

import csv
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np


@dataclass(frozen=True)
class QualityConfig:
    """Configurable quality thresholds for computer vision ingestion."""
    target_size: Tuple[int, int] = (224, 224)
    min_dimension: int = 64
    blur_threshold: float = 100.0  # Laplacian variance threshold
    min_luminance: float = 30.0    # Underexposure cutoff
    max_luminance: float = 225.0   # Overexposure cutoff
    rescale_range: Tuple[float, float] = (-1.0, 1.0)  # Standard MobileNetV2 input


@dataclass
class ImageInspectionResult:
    """Detailed diagnostic result for an inspected image."""
    filepath: str
    is_valid: bool
    status: str
    exclusion_reason: Optional[str]
    original_shape: Optional[Tuple[int, int, int]]
    laplacian_variance: Optional[float]
    mean_luminance: Optional[float]
    processed_shape: Optional[Tuple[int, int, int]]
    pixel_min: Optional[float]
    pixel_max: Optional[float]


def load_image_rgb(filepath: str | Path) -> Optional[np.ndarray]:
    """
    Safely load an image from disk and convert BGR to RGB.
    Returns None if the image file cannot be read, decoded, or is corrupted.
    """
    path_str = str(filepath)
    if not os.path.isfile(path_str):
        return None

    try:
        # cv2.imread handles common formats: jpg, png, webp, bmp, tif
        # Use cv2.imdecode to safely handle Windows unicode paths if needed
        data = np.fromfile(path_str, dtype=np.uint8)
        if data.size == 0:
            return None
        bgr = cv2.imdecode(data, cv2.IMREAD_COLOR)
        if bgr is None:
            return None
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        return rgb
    except Exception:
        return None


def calculate_blur_variance(image_rgb: np.ndarray) -> float:
    """Calculate the Laplacian variance of an RGB image in grayscale."""
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    return variance


def calculate_mean_luminance(image_rgb: np.ndarray) -> float:
    """Calculate the mean luminance (Y channel or grayscale intensity)."""
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    mean_val = float(np.mean(gray))
    return mean_val


def resize_with_pad(
    image_rgb: np.ndarray,
    target_size: Tuple[int, int] = (224, 224),
    pad_color: Tuple[int, int, int] = (0, 0, 0)
) -> np.ndarray:
    """
    Resize image to target_size (height, width) with aspect-ratio-preserving
    letterbox padding, avoiding anisotropic distortion of physical features.
    """
    target_h, target_w = target_size
    orig_h, orig_w = image_rgb.shape[:2]

    if orig_h == 0 or orig_w == 0:
        raise ValueError("Invalid image dimensions (height or width is 0).")

    scale = min(target_h / orig_h, target_w / orig_w)
    new_h = max(1, int(orig_h * scale))
    new_w = max(1, int(orig_w * scale))

    # cv2.resize takes (width, height)
    interpolation = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
    resized = cv2.resize(image_rgb, (new_w, new_h), interpolation=interpolation)

    padded = np.full((target_h, target_w, 3), pad_color, dtype=np.uint8)
    top = (target_h - new_h) // 2
    left = (target_w - new_w) // 2

    padded[top:top + new_h, left:left + new_w] = resized
    return padded


def rescale_mobilenetv2_input(
    image_padded_uint8: np.ndarray,
    out_range: Tuple[float, float] = (-1.0, 1.0)
) -> np.ndarray:
    """
    Rescale uint8 RGB image [0, 255] to float32 range [-1.0, 1.0]
    as expected by standard MobileNetV2 preprocessing.
    """
    if image_padded_uint8.dtype != np.uint8:
        image_padded_uint8 = np.clip(image_padded_uint8, 0, 255).astype(np.uint8)

    float_img = image_padded_uint8.astype(np.float32)
    # Mapping [0, 255] -> [-1.0, 1.0]: (x / 127.5) - 1.0
    rescaled = (float_img / 127.5) - 1.0
    return rescaled


def inspect_and_preprocess_image(
    filepath: str | Path,
    config: QualityConfig = QualityConfig()
) -> ImageInspectionResult:
    """
    Safely inspect, validate, and preprocess a single image file.
    Does NOT throw exceptions on corrupt, unreadable, or invalid files.
    """
    path_str = str(filepath)
    raw_rgb = load_image_rgb(path_str)

    if raw_rgb is None:
        return ImageInspectionResult(
            filepath=path_str,
            is_valid=False,
            status="EXCLUDED_CORRUPT_OR_UNREADABLE",
            exclusion_reason="Failed to decode image data into RGB array (corrupt or unreadable).",
            original_shape=None,
            laplacian_variance=None,
            mean_luminance=None,
            processed_shape=None,
            pixel_min=None,
            pixel_max=None
        )

    orig_h, orig_w, orig_c = raw_rgb.shape

    # Check minimum dimensions
    if orig_h < config.min_dimension or orig_w < config.min_dimension:
        return ImageInspectionResult(
            filepath=path_str,
            is_valid=False,
            status="EXCLUDED_DIMENSION_OUTLIER",
            exclusion_reason=f"Image dimensions ({orig_w}x{orig_h}) below minimum threshold ({config.min_dimension}px).",
            original_shape=(orig_h, orig_w, orig_c),
            laplacian_variance=None,
            mean_luminance=None,
            processed_shape=None,
            pixel_min=None,
            pixel_max=None
        )

    # Diagnostics
    blur_var = calculate_blur_variance(raw_rgb)
    mean_lum = calculate_mean_luminance(raw_rgb)

    # Check blur
    if blur_var < config.blur_threshold:
        return ImageInspectionResult(
            filepath=path_str,
            is_valid=False,
            status="EXCLUDED_BLUR_THRESHOLD",
            exclusion_reason=f"Laplacian variance {blur_var:.2f} below blur threshold {config.blur_threshold:.2f}.",
            original_shape=(orig_h, orig_w, orig_c),
            laplacian_variance=blur_var,
            mean_luminance=mean_lum,
            processed_shape=None,
            pixel_min=None,
            pixel_max=None
        )

    # Check luminance
    if mean_lum < config.min_luminance:
        return ImageInspectionResult(
            filepath=path_str,
            is_valid=False,
            status="EXCLUDED_UNDEREXPOSURE",
            exclusion_reason=f"Mean luminance {mean_lum:.2f} below minimum threshold {config.min_luminance:.2f}.",
            original_shape=(orig_h, orig_w, orig_c),
            laplacian_variance=blur_var,
            mean_luminance=mean_lum,
            processed_shape=None,
            pixel_min=None,
            pixel_max=None
        )

    if mean_lum > config.max_luminance:
        return ImageInspectionResult(
            filepath=path_str,
            is_valid=False,
            status="EXCLUDED_OVEREXPOSURE",
            exclusion_reason=f"Mean luminance {mean_lum:.2f} exceeds maximum threshold {config.max_luminance:.2f}.",
            original_shape=(orig_h, orig_w, orig_c),
            laplacian_variance=blur_var,
            mean_luminance=mean_lum,
            processed_shape=None,
            pixel_min=None,
            pixel_max=None
        )

    # Successful validation: perform letterbox and rescaling
    padded_uint8 = resize_with_pad(raw_rgb, target_size=config.target_size)
    processed = rescale_mobilenetv2_input(padded_uint8, out_range=config.rescale_range)

    return ImageInspectionResult(
        filepath=path_str,
        is_valid=True,
        status="PASSED",
        exclusion_reason=None,
        original_shape=(orig_h, orig_w, orig_c),
        laplacian_variance=round(blur_var, 3),
        mean_luminance=round(mean_lum, 3),
        processed_shape=processed.shape,
        pixel_min=round(float(processed.min()), 4),
        pixel_max=round(float(processed.max()), 4)
    )


def build_image_manifest(
    image_paths: List[str | Path],
    config: QualityConfig = QualityConfig(),
    output_manifest_path: Optional[str | Path] = None
) -> Dict[str, Any]:
    """
    Builds a reproducible manifest and audit report across a list of image paths.
    Does not modify or delete any original files.
    """
    results: List[ImageInspectionResult] = []
    passed_count = 0
    excluded_count = 0
    reasons_counter: Dict[str, int] = {}

    for path in image_paths:
        res = inspect_and_preprocess_image(path, config=config)
        results.append(res)
        if res.is_valid:
            passed_count += 1
        else:
            excluded_count += 1
            reason = res.status
            reasons_counter[reason] = reasons_counter.get(reason, 0) + 1

    manifest = {
        "total_evaluated": len(image_paths),
        "passed_count": passed_count,
        "excluded_count": excluded_count,
        "pass_rate": round(passed_count / len(image_paths), 4) if image_paths else 0.0,
        "quality_config": {
            "target_size": list(config.target_size),
            "min_dimension": config.min_dimension,
            "blur_threshold": config.blur_threshold,
            "min_luminance": config.min_luminance,
            "max_luminance": config.max_luminance,
            "rescale_range": list(config.rescale_range),
        },
        "exclusions_by_status": reasons_counter,
        "records": [asdict(r) for r in results]
    }

    if output_manifest_path:
        out_p = Path(output_manifest_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

    return manifest
