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
