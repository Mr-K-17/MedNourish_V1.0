"""
Schemas for MedScan Image Quality & Blended Inference Pipeline.
==============================================================
Spec: Phase 3 (c)
- Regional symptom checklist
- Quality check response
- Blended inference response adhering to scoring_service schema
- Kind: 'medscan_blend', 'image_only', 'reference_match'
- Percentage kind: 'Image model %', 'MedScan blend %', 'Reference match %'
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChecklistItem(BaseModel):
    tag: str = Field(..., description="Canonical symptom tag identifier")
    label: str = Field(..., description="Clinical plain-language label")


class ChecklistResponse(BaseModel):
    body_region: str = Field(..., description="Anatomical body region")
    items: List[ChecklistItem] = Field(..., description="6-8 discriminative symptoms for regional follow-up")


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


class ContributingRowItem(BaseModel):
    class_label: str
    body_region: str
    category: Optional[str] = None
    vitamin_deficiency: Optional[str] = None
    row_match_percentage: float
    matched_tags: List[str]
    match_count: int
    total_condition_tags: int


class MedScanNutrientScore(BaseModel):
    nutrient: str = Field(..., description="Nutrient or vitamin group")
    percentage: float = Field(..., description="Blended or model match percentage (0-95%)")
    percentage_kind: str = Field(..., description="'MedScan blend %', 'Image model %', or 'Reference match %'")
    percentage_explanation: str = Field(..., description="Honest transparent calculation explanation")
    image_percentage: Optional[float] = Field(None, description="Image model % contribution")
    reference_percentage: Optional[float] = Field(None, description="Reference match % contribution")
    risk_band: str = Field(..., description="High (>=60), Moderate (30-59), or Low (<30)")
    risk_band_label: str = Field(
        "Demo risk band (heuristic, not clinical)", description="Mandatory label per C-35"
    )
    matched_tags: List[str] = Field(default_factory=list)
    contributing_rows: List[Dict[str, Any]] = Field(default_factory=list)
    kind: str = Field(..., description="'medscan_blend', 'image_only', or 'reference_match'")


class MedScanBlendResponse(BaseModel):
    status: str = Field(..., description="'MATCHES_FOUND' or 'INSUFFICIENT_INFORMATION'")
    message: str = Field(..., description="Clinical-safety notice or summary message")
    disclaimer: str = Field(..., description="Educational prototype disclaimer")
    nutrient_scores: List[MedScanNutrientScore] = Field(..., description="Ranked nutrient groups")
    matched_entries: List[Dict[str, Any]] = Field(default_factory=list)
    unmatched_user_tags: List[str] = Field(default_factory=list)
    kind: str = Field("medscan_blend", description="Explicit source identifier")
    shortcut_flag: bool = Field(False, description="Whether visual shortcut penalty (w_img=0.25) was applied")
    w_img: float = Field(0.5, description="Weight given to image model evidence")
    saved_report_id: Optional[str] = Field(None, description="ID of auto-saved report in reports table")
    quality_passed: bool = Field(True, description="Whether image passed quality gating")
