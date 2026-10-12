"""Reports and Saved Summaries API endpoints.

Implements M1B.3:
- POST /v1/reports/summaries: Save reference match summary
- GET /v1/reports/summaries: List user's saved summaries
- GET /v1/reports/summaries/{summary_id}: Retrieve detailed saved summary
- DELETE /v1/reports/summaries/{summary_id}: Delete single saved summary

Strictly adheres to:
- PROF-02, SEC-01: Ownership derived exclusively from authenticated token (current_user.uid)
- REPORT-01, REPORT-04: Match snapshot, package & matcher versioning
- SAFE-01, SAF-07: Educational prototype disclaimer preserved
- SAF-17: Reference match summary, no clinical risk scores or probabilities
"""

import json
import logging
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.auth import AuthenticatedUser, get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.user import SavedSummary
from app.schemas.reports import (
    DeleteSummaryResponse,
    SaveSummaryRequest,
    SavedSummariesListResponse,
    SavedSummaryDetail,
    SavedSummaryItem,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/reports/summaries", response_model=SavedSummaryDetail, status_code=status.HTTP_201_CREATED)
def save_summary(
    payload: SaveSummaryRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Saves a completed reference match summary for the authenticated user.

    User ID is derived exclusively from the verified token.
    """
    summary_id = f"sum_{uuid.uuid4().hex[:16]}"
    selected_tags_json = json.dumps(payload.selected_tags)
    matched_entries_data = [item.model_dump() for item in payload.matched_entries]
    matched_entries_json = json.dumps(matched_entries_data)

    disclaimer = (
        "MEDNOURISH is an educational prototype. Results are reference-table matches and general health education, "
        "never medical diagnoses, predictions, or risk assessments. Discuss any symptom concerns with a qualified clinician."
    )

    db_item = SavedSummary(
        id=summary_id,
        user_id=current_user.uid,
        session_type=payload.session_type,
        body_region_filter=payload.body_region_filter,
        selected_tags_json=selected_tags_json,
        matched_entries_json=matched_entries_json,
        match_count_total=len(payload.matched_entries),
        package_version=payload.package_version,
        matcher_version=payload.matcher_version,
        review_status="unreviewed draft",
        disclaimer=disclaimer,
    )

    try:
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
    except Exception as exc:
        db.rollback()
        logger.error("Database error saving summary: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Failed to save summary.",
        )

    top_defs = list({item.vitamin_deficiency_association for item in payload.matched_entries})[:3]

    return SavedSummaryDetail(
        id=db_item.id,
        session_type=db_item.session_type,
        body_region_filter=db_item.body_region_filter,
        selected_tags=payload.selected_tags,
        match_count_total=db_item.match_count_total,
        top_deficiency_associations=top_defs,
        package_version=db_item.package_version,
        matcher_version=db_item.matcher_version,
        review_status=db_item.review_status,
        created_at=db_item.created_at,
        matched_entries=payload.matched_entries,
        disclaimer=db_item.disclaimer,
    )


@router.get("/reports/summaries", response_model=SavedSummariesListResponse)
def list_user_summaries(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists all saved summaries belonging strictly to the authenticated user."""
    try:
        records = (
            db.query(SavedSummary)
            .filter(SavedSummary.user_id == current_user.uid)
            .order_by(SavedSummary.created_at.desc())
            .all()
        )
    except Exception as exc:
        logger.error("Database error querying summaries: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Failed to list summaries.",
        )

    items: List[SavedSummaryItem] = []
    for r in records:
        try:
            tags = json.loads(r.selected_tags_json)
        except Exception:
            tags = []
        try:
            matched_list = json.loads(r.matched_entries_json)
            top_defs = list({m.get("vitamin_deficiency_association", "") for m in matched_list if m.get("vitamin_deficiency_association")})[:3]
        except Exception:
            top_defs = []

        items.append(
            SavedSummaryItem(
                id=r.id,
                session_type=r.session_type,
                body_region_filter=r.body_region_filter,
                selected_tags=tags,
                match_count_total=r.match_count_total,
                top_deficiency_associations=top_defs,
                package_version=r.package_version,
                matcher_version=r.matcher_version,
                review_status=r.review_status,
                created_at=r.created_at,
            )
        )

    return SavedSummariesListResponse(summaries=items, total_count=len(items))


@router.get("/reports/summaries/{summary_id}", response_model=SavedSummaryDetail)
def get_summary_detail(
    summary_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves full detail of a saved summary.

    Enforces ownership check: User A cannot read User B's summary (404/403).
    """
    try:
        record = db.query(SavedSummary).filter(SavedSummary.id == summary_id).first()
    except Exception as exc:
        logger.error("Database error retrieving summary: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Failed to load summary.",
        )

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved summary not found.",
        )

    # Ownership enforcement (PROF-02, SEC-01)
    if record.user_id != current_user.uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not have permission to view this summary.",
        )

    try:
        tags = json.loads(record.selected_tags_json)
        matched_entries = json.loads(record.matched_entries_json)
    except Exception as exc:
        logger.error("Error decoding saved summary JSON: %s", exc)
        tags = []
        matched_entries = []

    top_defs = list({m.get("vitamin_deficiency_association", "") for m in matched_entries if m.get("vitamin_deficiency_association")})[:3]

    return SavedSummaryDetail(
        id=record.id,
        session_type=record.session_type,
        body_region_filter=record.body_region_filter,
        selected_tags=tags,
        match_count_total=record.match_count_total,
        top_deficiency_associations=top_defs,
        package_version=record.package_version,
        matcher_version=record.matcher_version,
        review_status=record.review_status,
        created_at=record.created_at,
        matched_entries=matched_entries,
        disclaimer=record.disclaimer,
    )


@router.delete("/reports/summaries/{summary_id}", response_model=DeleteSummaryResponse)
def delete_summary(
    summary_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Deletes a saved summary belonging to the authenticated user.

    Enforces ownership check: User A cannot delete User B's summary.
    """
    try:
        record = db.query(SavedSummary).filter(SavedSummary.id == summary_id).first()
    except Exception as exc:
        logger.error("Database error during summary deletion: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Failed to delete summary.",
        )

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved summary not found.",
        )

    # Ownership check
    if record.user_id != current_user.uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not have permission to delete this summary.",
        )

    try:
        db.delete(record)
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error("Failed to commit summary deletion: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database error deleting summary.",
        )

    return DeleteSummaryResponse(
        status="deleted",
        id=summary_id,
        message="Saved summary successfully deleted.",
    )
