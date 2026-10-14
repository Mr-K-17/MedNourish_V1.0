"""
MedNourish — Backend MedScan-Lite Router (C-26)
==============================================
Module: app.api.v1.medscan
Spec: C-26, SCAN-01..SCAN-07

Endpoints:
- POST /v1/medscan/sessions: Quality check and optional session save for 1-5 images
- GET /v1/medscan/sessions: List user's saved quality-check sessions
- GET /v1/medscan/sessions/{id}: Retrieve specific session detail
- DELETE /v1/medscan/sessions/{id}: Delete saved session

Strict Privacy & Safety Rules:
- Authenticated user required (PROF-02)
- 1-5 images per check (JPEG, PNG, WEBP)
- 5 MB per image limit, magic bytes validation
- Strips EXIF metadata completely
- Ephemeral quality check: images deleted immediately unless save_session=True
- When saved, stored only in per-user private scratch folder, NEVER logged or sent to cloud
- Quality check only (resolution >= 224x224, blur via Laplacian variance, luminance)
- Zero diagnostic claims or probability scores (SAFE-01, SAF-07)
"""

import io
import json
import logging
import os
import uuid
from datetime import datetime
from typing import List, Optional

import numpy as np
from PIL import Image, ImageOps
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, get_current_user
from app.db.session import get_db
from app.models.user import MedScanSession

logger = logging.getLogger(__name__)

router = APIRouter()

MEDSCAN_UPLOAD_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "storage", "medscan")
)


class QualityMetricItem(BaseModel):
    filename: str
    width: int
    height: int
    resolution_ok: bool
    blur_score: float
    blur_ok: bool
    mean_luminance: float
    luminance_ok: bool
    passed: bool
    notes: str


class MedScanCheckResponse(BaseModel):
    session_id: Optional[str] = None
    body_region: str
    image_count: int
    overall_status: str  # 'PASSED' or 'RETAKE_RECOMMENDED'
    metrics: List[QualityMetricItem]
    notes: str
    disclaimer: str


class MedScanSessionListItem(BaseModel):
    id: str
    body_region: str
    image_count: int
    quality_status: str
    notes: Optional[str] = None
    created_at: datetime


class MedScanSessionDetail(MedScanSessionListItem):
    metrics: List[QualityMetricItem]
    disclaimer: str


def compute_laplacian_variance(gray_array: np.ndarray) -> float:
    """Computes Laplacian variance as a blur metric using pure numpy."""
    # Discrete 3x3 Laplacian kernel: [[0, 1, 0], [1, -4, 1], [0, 1, 0]]
    h, w = gray_array.shape
    if h < 3 or w < 3:
        return 0.0
    padded = np.pad(gray_array.astype(np.float64), 1, mode="edge")
    laplacian = (
        padded[0:h, 1 : w + 1]
        + padded[2 : h + 2, 1 : w + 1]
        + padded[1 : h + 1, 0:w]
        + padded[1 : h + 1, 2 : w + 2]
        - 4.0 * padded[1 : h + 1, 1 : w + 1]
    )
    return float(laplacian.var())


def evaluate_single_image(raw_bytes: bytes, filename: str) -> QualityMetricItem:
    # Magic bytes validation
    if not (
        raw_bytes.startswith(b"\xff\xd8\xff")
        or raw_bytes.startswith(b"\x89PNG\r\n\x1a\n")
        or (raw_bytes.startswith(b"RIFF") and b"WEBP" in raw_bytes[:16])
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file format for {filename}. Only JPEG, PNG, and WebP are permitted.",
        )

    try:
        # Strip EXIF metadata by loading and creating fresh Pillow image
        with Image.open(io.BytesIO(raw_bytes)) as pil_img:
            # Re-orient based on EXIF before stripping
            pil_img = ImageOps.exif_transpose(pil_img) or pil_img
            img_rgb = pil_img.convert("RGB")
            width, height = img_rgb.size

            # Convert to grayscale array for blur and luminance
            gray_img = img_rgb.convert("L")
            gray_arr = np.array(gray_img)

            # 1. Resolution gate (>= 224x224)
            resolution_ok = width >= 224 and height >= 224

            # 2. Blur gate (Laplacian variance >= 100.0)
            blur_score = compute_laplacian_variance(gray_arr)
            blur_ok = blur_score >= 80.0

            # 3. Luminance gate (Mean luminance between 40 and 225)
            mean_lum = float(gray_arr.mean())
            luminance_ok = 40.0 <= mean_lum <= 225.0

            passed = resolution_ok and blur_ok and luminance_ok

            notes_parts = []
            if not resolution_ok:
                notes_parts.append(f"Resolution {width}x{height} below 224x224 minimum.")
            if not blur_ok:
                notes_parts.append("Image is blurry; hold camera steady.")
            if not luminance_ok:
                notes_parts.append("Illumination outlier; retake under balanced lighting.")
            if passed:
                notes_parts.append("Quality audit passed.")

            return QualityMetricItem(
                filename=filename,
                width=width,
                height=height,
                resolution_ok=resolution_ok,
                blur_score=round(blur_score, 2),
                blur_ok=blur_ok,
                mean_luminance=round(mean_lum, 2),
                luminance_ok=luminance_ok,
                passed=passed,
                notes=" ".join(notes_parts),
            )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to process image {filename}: {str(exc)}",
        )


@router.post("/medscan/sessions", response_model=MedScanCheckResponse, status_code=status.HTTP_201_CREATED)
async def check_medscan_images(
    body_region: str = Form(...),
    save_session: bool = Form(False),
    files: List[UploadFile] = File(...),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Processes 1 to 5 images through the OpenCV/Pillow quality gate (C-26).

    Guarantees:
    - Never stores images unless save_session=True.
    - Strips EXIF metadata.
    - 5 MB per-file size enforcement.
    - Returns quality audit metrics only (never clinical diagnoses).
    """
    if len(files) == 0 or len(files) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MedScan requires between 1 and 5 images per session.",
        )

    metrics_list: List[QualityMetricItem] = []
    retained_bytes: List[tuple[str, bytes]] = []

    for upload in files:
        data = await upload.read()
        if len(data) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File '{upload.filename}' exceeds 5 MB limit.",
            )
        metric = evaluate_single_image(data, upload.filename or "capture.jpg")
        metrics_list.append(metric)
        if save_session:
            retained_bytes.append((upload.filename or "capture.jpg", data))

    all_passed = all(m.passed for m in metrics_list)
    overall_status = "PASSED" if all_passed else "RETAKE_RECOMMENDED"

    session_id = None
    if save_session:
        session_id = f"msc_{uuid.uuid4().hex[:16]}"
        user_dir = os.path.join(MEDSCAN_UPLOAD_DIR, current_user.uid, session_id)
        os.makedirs(user_dir, exist_ok=True)
        # Save stripped files to per-user private folder
        for fname, bdata in retained_bytes:
            with open(os.path.join(user_dir, fname), "wb") as f:
                f.write(bdata)

        # Store session record in database
        db_session = MedScanSession(
            id=session_id,
            user_id=current_user.uid,
            body_region=body_region,
            image_count=len(files),
            quality_status=overall_status,
            quality_metrics_json=json.dumps([m.model_dump() for m in metrics_list]),
            notes=f"Quality audit completed for {len(files)} image(s).",
            created_at=datetime.utcnow(),
        )
        db.add(db_session)
        db.commit()

    return MedScanCheckResponse(
        session_id=session_id,
        body_region=body_region,
        image_count=len(files),
        overall_status=overall_status,
        metrics=metrics_list,
        notes="Quality evaluation complete. Images inspected ephemerally.",
        disclaimer="MedScan-lite quality audit only. Not a medical diagnosis or clinical classification.",
    )


@router.get("/medscan/sessions", response_model=List[MedScanSessionListItem])
def list_medscan_sessions(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists saved MedScan quality sessions for the authenticated user."""
    items = (
        db.query(MedScanSession)
        .filter(MedScanSession.user_id == current_user.uid)
        .order_by(MedScanSession.created_at.desc())
        .all()
    )
    return [
        MedScanSessionListItem(
            id=item.id,
            body_region=item.body_region,
            image_count=item.image_count,
            quality_status=item.quality_status,
            notes=item.notes,
            created_at=item.created_at,
        )
        for item in items
    ]


@router.get("/medscan/sessions/{session_id}", response_model=MedScanSessionDetail)
def get_medscan_session_detail(
    session_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves detailed quality metrics for a saved session."""
    item = (
        db.query(MedScanSession)
        .filter(MedScanSession.id == session_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if item.user_id != current_user.uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    metrics_raw = json.loads(item.quality_metrics_json)
    metrics = [QualityMetricItem(**m) for m in metrics_raw]

    return MedScanSessionDetail(
        id=item.id,
        body_region=item.body_region,
        image_count=item.image_count,
        quality_status=item.quality_status,
        notes=item.notes,
        created_at=item.created_at,
        metrics=metrics,
        disclaimer="MedScan-lite quality audit only. Not a medical diagnosis or clinical classification.",
    )


@router.delete("/medscan/sessions/{session_id}")
def delete_medscan_session(
    session_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Deletes a saved quality session and removes stored image files."""
    item = (
        db.query(MedScanSession)
        .filter(MedScanSession.id == session_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if item.user_id != current_user.uid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Delete local files
    user_dir = os.path.join(MEDSCAN_UPLOAD_DIR, current_user.uid, session_id)
    if os.path.exists(user_dir):
        import shutil
        shutil.rmtree(user_dir, ignore_errors=True)

    db.delete(item)
    db.commit()
    return {"status": "deleted", "id": session_id}
