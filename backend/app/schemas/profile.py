"""Pydantic schemas for Profile and Consent operations.

Strictly enforces:
- Adults 18+ only (SAF-10, C-01)
- Never collects or stores Date of Birth or age (C-21, PROF-01)
- Versioned explicit consent tracking (AUTH-03)
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ConsentRequest(BaseModel):
    """Schema for recording user consent and adult confirmation."""

    is_adult_confirmed: bool = Field(
        ...,
        description="Explicit declaration that user is an adult aged 18 or above (C-01, SAF-10).",
    )
    terms_consent_version: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Version identifier of agreed consent terms (e.g. 'v1.0').",
    )

    @field_validator("is_adult_confirmed")
    @classmethod
    def validate_adult(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Application is strictly for adults aged 18 and above. Adult confirmation is required.")
        return v


class ProfileCreateRequest(BaseModel):
    """Schema for creating the initial minimal profile."""

    is_adult_confirmed: bool = Field(
        ...,
        description="Explicit declaration that user is an adult aged 18 or above (C-01, SAF-10).",
    )
    terms_consent_version: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Version identifier of agreed terms (e.g. 'v1.0').",
    )
    display_name: Optional[str] = Field(None, max_length=100)
    gender: Optional[str] = Field(None, max_length=30)
    height_cm: Optional[float] = Field(None, ge=50.0, le=280.0)
    weight_kg: Optional[float] = Field(None, ge=20.0, le=450.0)

    @field_validator("is_adult_confirmed")
    @classmethod
    def validate_adult(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Application is strictly for adults aged 18 and above. Adult confirmation is required.")
        return v


class ProfileUpdateRequest(BaseModel):
    """Schema for updating optional profile attributes."""

    display_name: Optional[str] = Field(None, max_length=100)
    gender: Optional[str] = Field(None, max_length=30)
    height_cm: Optional[float] = Field(None, ge=50.0, le=280.0)
    weight_kg: Optional[float] = Field(None, ge=20.0, le=450.0)


class ProfileResponse(BaseModel):
    """Safe profile response representation."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    display_name: Optional[str] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    is_adult_confirmed: bool
    terms_consent_version: str
    created_at: datetime
    updated_at: datetime


class AccountDeletionResponse(BaseModel):
    """Response after deleting account and profile data."""

    status: str = "deleted"
    message: str = "User profile, consent records, and authentication account successfully deleted."
