"""Relational models for MySQL application storage.

Strictly adheres to C-01 (18+ adults), C-21 (minimal profile), and PRD PROF-01.
Never stores date of birth or infers user age.
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime
from app.db.session import Base


class UserProfile(Base):
    """User profile table storing minimal non-identifiable demographic parameters."""

    __tablename__ = "user_profiles"

    # User ID matches the verified Firebase Authentication UID
    id = Column(String(128), primary_key=True, index=True)
    display_name = Column(String(100), nullable=True)
    gender = Column(String(30), nullable=True)  # Optional self-reported
    height_cm = Column(Float, nullable=True)    # In cm
    weight_kg = Column(Float, nullable=True)    # In kg

    # Verification and consent flags (SAF-10, C-21)
    is_adult_confirmed = Column(Boolean, default=False, nullable=False)
    terms_consent_version = Column(String(20), nullable=False)
    consent_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class UserConsentLog(Base):
    """Audit log of consent lifecycle events (consent recorded, updated, withdrawn)."""

    __tablename__ = "user_consent_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(128), index=True, nullable=False)
    event_type = Column(String(50), nullable=False)  # 'CONSENT_GRANTED', 'CONSENT_REVOKED'
    consent_version = Column(String(20), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


class SavedSummary(Base):
    """Stores saved reference match summaries for Files & Reports.

    Adheres strictly to:
    - PROF-02: Keyed to authenticated user_id
    - REPORT-01: Reference-table match snapshot, never clinical risk scores or probabilities
    - REPORT-04: Records package_version and matcher_version
    - SAFE-01, SAF-07: Records educational disclaimer and review status
    - AUTH-05: Deleted when account is deleted
    """

    __tablename__ = "saved_summaries"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(128), index=True, nullable=False)
    session_type = Column(String(32), default="Explorer", nullable=False)  # 'Explorer' or 'MedBot'
    body_region_filter = Column(String(32), nullable=True)
    selected_tags_json = Column(String(2048), nullable=False)  # JSON-encoded array of selected tags
    matched_entries_json = Column(String(8192), nullable=False)  # JSON-encoded array of matched reference summaries
    match_count_total = Column(Integer, default=0, nullable=False)
    package_version = Column(String(32), nullable=False)
    matcher_version = Column(String(32), nullable=False)
    review_status = Column(String(32), default="unreviewed draft", nullable=False)
    disclaimer = Column(String(1024), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class CarePlanItem(Base):
    """Stores user-created general wellness tasks for CarePlan (M1B.5).

    Adheres strictly to:
    - CARE-01, CARE-02: User-created general wellness tasks (water, food, exercise, sleep).
      Never medication reminders or supplement/drug suggestions (C-08, C-22).
    - CARE-03: Tracks completion state and completion timestamps.
    - PROF-02: Keyed to authenticated user_id; data isolation enforced.
    - AUTH-05: Cascading delete on user account deletion.
    """

    __tablename__ = "care_plan_items"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(128), index=True, nullable=False)
    title = Column(String(140), nullable=False)
    category = Column(String(32), default="general", nullable=False)  # water, food, exercise, sleep, general
    target_frequency = Column(String(64), nullable=True)  # e.g., 'daily', 'twice daily'
    reminder_time = Column(String(16), nullable=True)  # e.g., '08:00', '14:00'
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class MedScanSession(Base):
    """Stores saved MedScan-lite quality check sessions (C-26).

    Guarantees:
    - PROF-02: Keyed to authenticated user_id
    - SCAN-02: Records image quality metrics (resolution, illumination, blur status)
    - SCAN-05: Ephemeral check by default; only saved when user explicitly requests
    - AUTH-05: Cascading delete on user account deletion
    - Zero image bytes or diagnostic claims logged/stored in relational database
    """

    __tablename__ = "medscan_sessions"

    id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(128), index=True, nullable=False)
    body_region = Column(String(32), nullable=False)
    image_count = Column(Integer, default=1, nullable=False)
    quality_status = Column(String(32), nullable=False)  # 'PASSED', 'RETAKE_RECOMMENDED'
    quality_metrics_json = Column(String(2048), nullable=False)
    notes = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

