"""MedBot Guided Questionnaire API endpoints.

Implements M1B.4:
- GET /v1/medbot/questions: returns question sequence for requested mode ('simple' or 'standard')
- POST /v1/medbot/evaluate: processes user answers, performs deterministic matching, and returns reference summary
- POST /v1/medbot/save: persists MedBot assessment into saved summaries (Files & Reports)

Adheres strictly to:
- MEDBOT-01 to MEDBOT-06, MEDBOT-10
- SAF-01, SAF-03, SAF-06, SAF-07, SAF-17
- Requires authenticated user session (401 if unauthenticated)
- Zero free-text input, zero diagnosis or medication recommendations
"""

import json
import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.auth import AuthenticatedUser, get_current_user
from app.db.session import get_db
from app.models.user import SavedSummary
from app.schemas.medbot import (
    MedBotEvaluateRequest,
    MedBotEvaluateResponse,
    QuestionnaireConfigResponse,
)
from app.schemas.reports import SaveSummaryRequest, SavedSummaryDetail
from app.services.knowledge_service import (
    MATCHER_VERSION,
    PACKAGE_VERSION,
)
from app.services.medbot_service import medbot_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/medbot/questions", response_model=QuestionnaireConfigResponse)
def get_medbot_questions(
    mode: str = Query("simple", description="Questionnaire mode ('simple' or 'standard')"),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Retrieves scripted question sequence for requested mode.

    Requires authenticated session.
    """
    try:
        return medbot_service.get_questionnaire_config(mode=mode)
    except Exception as exc:
        logger.error("Error retrieving MedBot questions: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating questionnaire configuration.",
        )


@router.post("/medbot/evaluate", response_model=MedBotEvaluateResponse)
def evaluate_medbot_questionnaire(
    payload: MedBotEvaluateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Evaluates questionnaire answers and returns deterministic reference match summary.

    Requires authenticated session.
    """
    try:
        return medbot_service.evaluate_answers(mode=payload.mode, answers=payload.answers)
    except Exception as exc:
        logger.error("Error evaluating MedBot answers: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error evaluating questionnaire answers.",
        )


@router.post(
    "/medbot/save",
    response_model=SavedSummaryDetail,
    status_code=status.HTTP_201_CREATED,
)
def save_medbot_assessment(
    payload: SaveSummaryRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Saves a completed MedBot assessment summary to user's history in Files & Reports.

    Reuses PROF-02 / REPORT-01 persistence with session_type='MedBot'.
    """
    summary_id = f"sum_{uuid.uuid4().hex[:16]}"
    disclaimer = (
        "MEDNOURISH is an educational prototype. Results are reference-table matches and general health education, "
        "never medical diagnoses, predictions, or risk assessments. Discuss any symptom concerns with a qualified clinician."
    )

    matched_dicts = [entry.model_dump() for entry in payload.matched_entries]

    record = SavedSummary(
        id=summary_id,
        user_id=current_user.uid,
        session_type="MedBot",
        body_region_filter=payload.body_region_filter,
        selected_tags_json=json.dumps(payload.selected_tags),
        matched_entries_json=json.dumps(matched_dicts),
        match_count_total=len(payload.matched_entries),
        package_version=payload.package_version,
        matcher_version=payload.matcher_version,
        review_status="unreviewed draft",
        disclaimer=disclaimer,
    )

    try:
        db.add(record)
        db.commit()
        db.refresh(record)
    except Exception as exc:
        db.rollback()
        logger.error("Database error saving MedBot assessment: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Failed to save assessment summary.",
        )

    return SavedSummaryDetail(
        id=record.id,
        user_id=record.user_id,
        session_type=record.session_type,
        body_region_filter=record.body_region_filter,
        selected_tags=payload.selected_tags,
        matched_entries=payload.matched_entries,
        match_count_total=record.match_count_total,
        package_version=record.package_version,
        matcher_version=record.matcher_version,
        review_status=record.review_status,
        disclaimer=record.disclaimer,
        created_at=record.created_at,
    )
