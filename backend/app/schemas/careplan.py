"""CarePlan Pydantic Schemas (M1B.5).

Adheres strictly to:
- CARE-01, CARE-02: User-created general wellness tasks (water, food, exercise, sleep).
  Prohibits medication reminders, drug prescriptions, and supplement suggestions (C-08, C-22).
- CARE-03: Tracks completion state and completion timestamps.
- CARE-04: In-app reminder configuration with mandatory disclaimer notice.
- PROF-02: Keyed to authenticated user_id; data isolation enforced.
"""

import re
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

# Prohibited medical/medication terms in CarePlan tasks per C-08, C-22, SAF-02
PROHIBITED_MEDICATION_TERMS = {
    "pill",
    "pills",
    "medication",
    "medicine",
    "dose",
    "dosage",
    "prescription",
    "prescribe",
    "drug",
    "supplement",
    "tablet",
    "capsule",
    "injection",
    "antibiotic",
    "steroid",
    "statin",
    "insulin",
}

ALLOWED_CATEGORIES = {"water", "food", "exercise", "sleep", "general"}


class CarePlanItemCreate(BaseModel):
    title: str = Field(
        ..., min_length=2, max_length=140, description="Title of the wellness task"
    )
    category: str = Field(
        "general", description="Wellness category: water, food, exercise, sleep, general"
    )
    target_frequency: Optional[str] = Field(
        "daily", max_length=64, description="Target frequency (e.g. 'daily', 'twice daily')"
    )
    reminder_time: Optional[str] = Field(
        None, max_length=16, description="Optional 24h reminder time (HH:MM)"
    )

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        norm = v.lower().strip()
        if norm not in ALLOWED_CATEGORIES:
            raise ValueError(
                f"Invalid category '{v}'. Allowed categories: {sorted(list(ALLOWED_CATEGORIES))}"
            )
        return norm

    @field_validator("title")
    @classmethod
    def validate_no_medication_or_supplements(cls, v: str) -> str:
        words = re.findall(r"\b[a-zA-Z]+\b", v.lower())
        for word in words:
            if word in PROHIBITED_MEDICATION_TERMS:
                raise ValueError(
                    f"Medication or supplement reminders are not permitted in CarePlan (C-08, C-22). Prohibited term: '{word}'"
                )
        return v.strip()


class CarePlanItemUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=140)
    category: Optional[str] = None
    target_frequency: Optional[str] = Field(None, max_length=64)
    reminder_time: Optional[str] = Field(None, max_length=16)
    is_completed: Optional[bool] = None

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        norm = v.lower().strip()
        if norm not in ALLOWED_CATEGORIES:
            raise ValueError(f"Invalid category '{v}'. Allowed: {sorted(list(ALLOWED_CATEGORIES))}")
        return norm

    @field_validator("title")
    @classmethod
    def validate_no_medication_or_supplements(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        words = re.findall(r"\b[a-zA-Z]+\b", v.lower())
        for word in words:
            if word in PROHIBITED_MEDICATION_TERMS:
                raise ValueError(
                    f"Medication or supplement reminders are not permitted in CarePlan (C-08, C-22). Prohibited term: '{word}'"
                )
        return v.strip()


class CarePlanItemResponse(BaseModel):
    id: str = Field(..., description="Unique task identifier")
    title: str = Field(..., description="Task title")
    category: str = Field(..., description="Wellness category")
    target_frequency: Optional[str] = None
    reminder_time: Optional[str] = None
    is_completed: bool = Field(..., description="Completion state")
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    reminder_notice: str = Field(
        "Reminders only alert while this app is open in your browser.",
        description="Mandatory reminder limitation disclosure per CARE-04",
    )


class CarePlanListResponse(BaseModel):
    tasks: List[CarePlanItemResponse] = Field(default_factory=list)
    total_count: int
    completed_count: int
    reminder_notice: str = Field(
        "Reminders only alert while this app is open in your browser.",
        description="Mandatory reminder limitation disclosure per CARE-04",
    )
    disclaimer: str = Field(
        "CarePlan tasks are self-directed general wellness routines (hydration, food, exercise, sleep), not clinical treatments or medical prescriptions.",
        description="Educational prototype disclaimer",
    )


class CarePlanDeleteResponse(BaseModel):
    status: str = Field("deleted")
    id: str
    message: str
