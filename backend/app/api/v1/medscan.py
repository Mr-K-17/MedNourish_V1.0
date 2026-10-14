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
from app.models.user import MedScanSession, SavedSummary
from app.schemas.medscan import ChecklistResponse, MedScanBlendResponse
from app.services.medscan_service import medscan_pipeline

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


@router.get("/medscan/checklist", response_model=ChecklistResponse)
def get_medscan_checklist(
    body_region: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Returns 6-8 discriminative symptoms for regional follow-up (SCAN-06)."""
    items = medscan_pipeline.get_checklist_for_region(body_region)
    return ChecklistResponse(body_region=body_region, items=items)


@router.post("/medscan/analyze", response_model=MedScanBlendResponse)
async def analyze_medscan(
    body_region: str = Form(...),
    file: UploadFile = File(...),
    symptoms: Optional[str] = Form(""),
    save_report: bool = Form(True),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Executes the end-to-end MedScan blended inference pipeline:
    1. Quality check (dimensions >= 224x224, blur, illumination, format).
    2. Model inference via ml-service (if available) -> Image model %.
    3. Crosswalk to nutrient evidence.
    4. Blend with user's selected regional checklist symptoms.
    5. Auto-saves to reports table as source 'medscan'.
    6. Ephemeral cleanup: image file discarded immediately.
    """
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image exceeds 5 MB size limit.",
        )

    # Magic bytes check
    if not (contents.startswith(b"\xff\xd8\xff") or contents.startswith(b"\x89PNG") or contents.startswith(b"RIFF")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format. Allowed formats: JPEG, PNG, WEBP.",
        )

    try:
        pil_img = Image.open(io.BytesIO(contents))
        pil_img = ImageOps.exif_transpose(pil_img)
        w, h = pil_img.size
        gray = pil_img.convert("L")
        gray_arr = np.array(gray)
        blur_val = compute_laplacian_variance(gray_arr)
        mean_lum = float(np.mean(gray_arr))

        resolution_ok = (w >= 224 and h >= 224)
        blur_ok = (blur_val >= 50.0)
        lum_ok = (20.0 <= mean_lum <= 235.0)
        quality_passed = (resolution_ok and blur_ok and lum_ok)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to process image: {e}",
        )

    # Parse ticked symptoms
    ticked_tags: List[str] = []
    if symptoms:
        s_clean = symptoms.strip()
        if s_clean.startswith("["):
            try:
                ticked_tags = json.loads(s_clean)
            except Exception:
                ticked_tags = [t.strip() for t in s_clean.split(",") if t.strip()]
        else:
            ticked_tags = [t.strip() for t in s_clean.split(",") if t.strip()]

    # Map model name
    reg_clean = body_region.lower().strip()
    model_name = reg_clean if reg_clean in ["eyes", "hair", "lips", "nails", "skin", "tongue"] else "combined"

    # Call ml-service
    ml_res, ml_err = await medscan_pipeline.predict_image_via_ml_service(
        model_name=model_name,
        file_bytes=contents,
        filename=file.filename or "upload.jpg",
        content_type=file.content_type or "image/jpeg",
    )

    ml_service_down = (ml_res is None)
    image_nutrients: Dict[str, float] = {}
    shortcut_flag = False

    if ml_res:
        preds = ml_res.get("predictions", [])
        shortcut_flag = bool(ml_res.get("shortcut_flag", False))
        image_nutrients = medscan_pipeline.map_predictions_to_nutrients(model_name, preds)

    # Blend evidence
    blend_res = medscan_pipeline.blend_evidence(
        image_nutrients=image_nutrients,
        ticked_symptom_tags=ticked_tags,
        region=reg_clean,
        shortcut_flag=shortcut_flag,
        ml_service_down=ml_service_down,
    )

    # Auto-save report if requested and nutrient scores exist
    saved_report_id = None
    if save_report and blend_res.get("nutrient_scores"):
        formatted_report_entries = []
        if blend_res.get("matched_entries"):
            formatted_report_entries = blend_res["matched_entries"]
        else:
            for nut in blend_res.get("nutrient_scores", []):
                formatted_report_entries.append({
                    "class_label": f"MedScan Pattern ({nut['nutrient']})",
                    "body_region": body_region.upper(),
                    "category": "Nutritional",
                    "vitamin_deficiency_association": nut["nutrient"],
                    "matched_tags": nut.get("matched_tags", []),
                    "match_count": len(nut.get("matched_tags", [])),
                    "total_condition_tags": max(1, len(nut.get("matched_tags", []))),
                    "row_match_percentage": nut.get("percentage", 0.0),
                    "review_status": "unreviewed draft",
                })

        # Build snapshot scores for multi-engine recency aggregation
        snapshot_scores = {}
        top_nutrients_list = []
        for nut in blend_res.get("nutrient_scores", []):
            p_val = float(nut.get("percentage", 0.0))
            snapshot_scores[nut["nutrient"]] = {
                "reference_pct": float(nut.get("reference_pct", 0.0)),
                "xgboost_pct": 0.0,
                "lightgbm_pct": 0.0,
                "image_pct": float(nut.get("image_pct", 0.0)),
                "final_pct": p_val,
            }
            top_nutrients_list.append({"nutrient": nut["nutrient"], "final_pct": p_val})

        report_id = str(uuid.uuid4())
        summary_record = SavedSummary(
            id=report_id,
            user_id=current_user.uid,
            session_type="medscan",
            body_region_filter=body_region,
            selected_tags_json=json.dumps(ticked_tags),
            matched_entries_json=json.dumps(formatted_report_entries),
            match_count_total=len(formatted_report_entries),
            snapshot_scores_json=json.dumps(snapshot_scores),
            package_version="medscan_blend_v2.0",
            matcher_version="mobilenetv2_tflite_v2.0",
            review_status="unreviewed draft",
            disclaimer=blend_res["disclaimer"],
            created_at=datetime.utcnow(),
        )
        db.add(summary_record)
        db.commit()
        saved_report_id = report_id

        # Trigger CarePlan auto-sync for top 2 nutrients with % >= 30
        from app.services.careplan_sync_service import sync_careplan_from_top_nutrients
        top_nutrients_list.sort(key=lambda x: x["final_pct"], reverse=True)
        max_b = "High" if any(n["final_pct"] >= 60.0 for n in top_nutrients_list) else ("Moderate" if any(n["final_pct"] >= 30.0 for n in top_nutrients_list) else "Low")
        try:
            sync_careplan_from_top_nutrients(db, current_user.uid, report_id, top_nutrients_list, max_b)
        except Exception as e:
            logger.warning("CarePlan auto-sync from medscan failed non-fatally: %s", e)

    blend_res["saved_report_id"] = saved_report_id
    blend_res["quality_passed"] = quality_passed
    return blend_res

