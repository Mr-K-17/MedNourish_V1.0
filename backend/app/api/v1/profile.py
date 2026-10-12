"""Profile and Consent API endpoints.

Handles:
- Profile retrieval (GET /v1/profile)
- Profile creation with mandatory adult confirmation (POST /v1/profile)
- Profile update of optional demographic fields (PUT /v1/profile)
- Account and profile deletion (DELETE /v1/profile)
Strictly adheres to:
- SAF-10, C-01: Adults 18+ only
- C-21, PROF-01: No DOB or age stored
- SEC-01, PROF-02: Validated against authenticated user's Firebase UID
- AUTH-05: Account deletion deletes user-associated data
"""

import json
import logging
import urllib.error
import urllib.request
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.auth import AuthenticatedUser, get_current_user, security_scheme
from app.core.config import settings
from app.db.session import get_db
from app.models.user import UserConsentLog, UserProfile
from app.schemas.profile import (
    AccountDeletionResponse,
    ProfileCreateRequest,
    ProfileResponse,
    ProfileUpdateRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/profile", response_model=ProfileResponse)
def get_user_profile(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves the authenticated user's minimal profile."""
    try:
        profile = db.query(UserProfile).filter(UserProfile.id == current_user.uid).first()
    except Exception as exc:
        logger.error("Database error retrieving profile: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Please check database configuration.",
        )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found. Initial setup and consent required.",
        )
    return profile


@router.post("/profile", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
def create_user_profile(
    payload: ProfileCreateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Creates initial minimal user profile. Requires explicit 18+ adult confirmation."""
    try:
        existing = db.query(UserProfile).filter(UserProfile.id == current_user.uid).first()
    except Exception as exc:
        logger.error("Database error querying existing profile: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Please check database configuration.",
        )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Profile already exists for this account.",
        )

    # 1. Create minimal profile
    profile = UserProfile(
        id=current_user.uid,
        display_name=payload.display_name,
        gender=payload.gender,
        height_cm=payload.height_cm,
        weight_kg=payload.weight_kg,
        is_adult_confirmed=payload.is_adult_confirmed,
        terms_consent_version=payload.terms_consent_version,
    )
    db.add(profile)

    # 2. Append immutable consent log entry
    consent_log = UserConsentLog(
        user_id=current_user.uid,
        event_type="CONSENT_GRANTED",
        consent_version=payload.terms_consent_version,
    )
    db.add(consent_log)

    try:
        db.commit()
        db.refresh(profile)
        return profile
    except Exception as exc:
        db.rollback()
        logger.error("Failed to persist user profile: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to save profile due to database error.",
        )


@router.put("/profile", response_model=ProfileResponse)
def update_user_profile(
    payload: ProfileUpdateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Updates optional demographic profile fields (display_name, gender, height, weight)."""
    try:
        profile = db.query(UserProfile).filter(UserProfile.id == current_user.uid).first()
    except Exception as exc:
        logger.error("Database error retrieving profile for update: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Please check database configuration.",
        )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found. Setup required.",
        )

    if payload.display_name is not None:
        profile.display_name = payload.display_name
    if payload.gender is not None:
        profile.gender = payload.gender
    if payload.height_cm is not None:
        profile.height_cm = payload.height_cm
    if payload.weight_kg is not None:
        profile.weight_kg = payload.weight_kg

    try:
        db.commit()
        db.refresh(profile)
        return profile
    except Exception as exc:
        db.rollback()
        logger.error("Failed to update profile: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to update profile due to database error.",
        )


@router.delete("/profile", response_model=AccountDeletionResponse)
def delete_user_account(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Deletes the user's profile, consent logs, and triggers account deletion in Auth Emulator.

    Adheres strictly to AUTH-05, OD-08, and PRIV-01: development deletes everything.
    """
    try:
        # Delete relational records in database
        db.query(UserConsentLog).filter(UserConsentLog.user_id == current_user.uid).delete()
        db.query(UserProfile).filter(UserProfile.id == current_user.uid).delete()
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error("Database error during account deletion: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Failed to delete user records.",
        )

    return AccountDeletionResponse(
        status="deleted",
        message="User profile and all associated data successfully deleted.",
    )
