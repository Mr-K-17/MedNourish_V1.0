"""Pydantic schemas for Profile and Consent operations.

Strictly enforces:
- C-33: Age (1-120 integer), blood_type, conditions (18 options + None), other_condition (<=100 chars)
- SAF-10 / AUTH-03 / C-33: Demo consent checkbox replaces strict 18+ gate; under-18 advisory notice
- Date of Birth is NEVER collected or stored (age is an integer)
- Versioned explicit consent tracking (AUTH-03)
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ALLOWED_BLOOD_TYPES = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Unknown"]

ALLOWED_CONDITIONS = [
    "Type 2 diabetes",
    "Type 1 diabetes",
    "Hypertension",
    "Anemia",
    "Thyroid disorder",
    "Asthma",
    "Celiac disease",
    "Crohn's/IBD",
    "Irritable bowel syndrome",
    "Chronic kidney disease",
    "Liver disease",
    "Heart disease",
    "PCOS",
    "Osteoporosis",
    "Depression/anxiety",
    "Migraine",
    "Acid reflux/gastritis",
    "Lactose intolerance/food allergy",
    "None",
]


class ConsentRequest(BaseModel):
    """Schema for recording user consent and demo confirmation."""

    is_adult_confirmed: Optional[bool] = Field(
        None,
        description="Explicit declaration that user is an adult aged 18 or above (retained for backward compatibility).",
    )
    demo_consent_confirmed: bool = Field(
        True,
        description="Explicit agreement to educational demo terms (C-33).",
    )
    terms_consent_version: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Version identifier of agreed consent terms (e.g. 'v1.0').",
    )

    @model_validator(mode="after")
    def validate_consent(self) -> "ConsentRequest":
        if self.is_adult_confirmed is False and not self.demo_consent_confirmed:
            raise ValueError("Application requires educational demo consent.")
        return self


class ProfileCreateRequest(BaseModel):
    """Schema for creating the initial user profile (C-33 extended)."""

    is_adult_confirmed: Optional[bool] = Field(
        None,
        description="Explicit declaration that user is an adult aged 18 or above.",
    )
    demo_consent_confirmed: bool = Field(
        False,
        description="Explicit agreement to educational demo terms (C-33).",
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
    age: Optional[int] = Field(None, ge=1, le=120, description="Age in years (1-120).")
    blood_type: Optional[str] = Field(None, max_length=10)
    conditions: Optional[List[str]] = Field(None)
    other_condition: Optional[str] = Field(None, max_length=100)

    @field_validator("blood_type")
    @classmethod
    def validate_blood_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_BLOOD_TYPES:
            raise ValueError(f"Invalid blood_type '{v}'. Allowed values: {ALLOWED_BLOOD_TYPES}")
        return v

    @field_validator("conditions")
    @classmethod
    def validate_conditions(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None:
            for item in v:
                if item not in ALLOWED_CONDITIONS:
                    raise ValueError(f"Invalid condition '{item}'. Allowed values: {ALLOWED_CONDITIONS}")
        return v

    @model_validator(mode="after")
    def validate_consent_or_adult(self) -> "ProfileCreateRequest":
        # Valid if either demo_consent_confirmed is True or is_adult_confirmed is True
        if not self.demo_consent_confirmed and not self.is_adult_confirmed:
            raise ValueError("Application requires educational demo consent or adult confirmation.")
        return self


class ProfileUpdateRequest(BaseModel):
    """Schema for updating optional profile attributes."""

    display_name: Optional[str] = Field(None, max_length=100)
    gender: Optional[str] = Field(None, max_length=30)
    height_cm: Optional[float] = Field(None, ge=50.0, le=280.0)
    weight_kg: Optional[float] = Field(None, ge=20.0, le=450.0)
    age: Optional[int] = Field(None, ge=1, le=120)
    blood_type: Optional[str] = Field(None, max_length=10)
    conditions: Optional[List[str]] = None
    other_condition: Optional[str] = Field(None, max_length=100)

    @field_validator("blood_type")
    @classmethod
    def validate_blood_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_BLOOD_TYPES:
            raise ValueError(f"Invalid blood_type '{v}'. Allowed values: {ALLOWED_BLOOD_TYPES}")
        return v

    @field_validator("conditions")
    @classmethod
    def validate_conditions(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None:
            for item in v:
                if item not in ALLOWED_CONDITIONS:
                    raise ValueError(f"Invalid condition '{item}'. Allowed values: {ALLOWED_CONDITIONS}")
        return v


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
    age: Optional[int] = None
    blood_type: Optional[str] = None
    conditions: Optional[List[str]] = None
    other_condition: Optional[str] = None
    under_18_notice: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AccountDeletionResponse(BaseModel):
    """Response after deleting account and profile data."""

    status: str = "deleted"
    message: str = "User profile, consent records, and authentication account successfully deleted."
