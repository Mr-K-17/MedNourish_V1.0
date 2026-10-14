"""Schemas for Symptom Reference Explorer API.

Adheres strictly to:
- SAF-01, SAF-07: Educational prototype disclaimers
- SAF-06: Insufficient Information states
- C-34: Reference match %, Model %, Image model %
- C-35: Demo risk band High/Moderate/Low (heuristic, not clinical)
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class TagItem(BaseModel):
    tag: str = Field(..., description="Normalized tag identifier")
    label: str = Field(..., description="Display label for the symptom tag")


class CategoriesResponse(BaseModel):
    regions: List[str] = Field(..., description="List of available anatomical regions")
    tags_by_region: dict[str, List[TagItem]] = Field(
        ..., description="Available symptom tags grouped by anatomical region"
    )
    total_tags: int = Field(..., description="Total available nutritional symptom tags")
    package_version: str = Field(..., description="Version of the curated reference package")


class MatchRequest(BaseModel):
    selected_tags: List[str] = Field(
        ..., min_length=0, description="List of user selected symptom tags"
    )
    body_region_filter: Optional[str] = Field(
        None, description="Optional filter to restrict match to a specific region"
    )


class ContributingRow(BaseModel):
    class_label: str = Field(..., description="Canonical reference class identifier")
    body_region: str = Field(..., description="Anatomical body region")
    category: Optional[str] = Field(None, description="Nutritional category")
    vitamin_deficiency: Optional[str] = Field(None, description="Associated vitamin deficiency")
    row_match_percentage: float = Field(..., description="IDF-weighted match percentage for this row (0-95%)")
    matched_tags: List[str] = Field(..., description="Matched symptom tags")
    match_count: int = Field(..., description="Count of matched tags")
    total_condition_tags: int = Field(..., description="Total tags for condition")


class NutrientScore(BaseModel):
    nutrient: str = Field(..., description="Nutrient or vitamin group name")
    percentage: float = Field(..., description="Noisy-OR combined percentage (0-95%)")
    percentage_kind: str = Field("Reference match %", description="Explicit percentage kind per C-34")
    percentage_explanation: str = Field(
        "Deterministic coverage of reference database symptom patterns, not a clinical diagnosis or test.",
        description="Clear one-line explanation per C-34",
    )
    risk_band: str = Field(..., description="High (>=60), Moderate (30-59), or Low (<30)")
    risk_band_label: str = Field(
        "Demo risk band (heuristic, not clinical)", description="Mandatory label per C-35"
    )
    matched_tags: List[str] = Field(..., description="All tags contributing to this nutrient")
    contributing_rows: List[ContributingRow] = Field(
        default_factory=list, description="Underlying condition rows contributing to this nutrient"
    )
    kind: str = Field("reference_match", description="Internal score source tag")


class MatchedEntry(BaseModel):
    class_label: str = Field(..., description="Canonical reference class identifier")
    body_region: str = Field(..., description="Anatomical body region")
    category: str = Field(..., description="Nutritional category")
    vitamin_deficiency_association: str = Field(
        ..., description="Associated vitamin or nutrient deficiency reference"
    )
    matched_tags: List[str] = Field(..., description="Tags from user query that matched this entry")
    match_count: int = Field(..., description="Number of tags matched")
    total_condition_tags: int = Field(
        ..., description="Total reference tags documented for this condition class"
    )
    row_match_percentage: Optional[float] = Field(
        None, description="IDF-weighted match percentage (0-95%)"
    )
    review_status: str = Field(
        "unreviewed draft", description="Clinical review status per PV-17 / SAF-13"
    )


class MatchResponse(BaseModel):
    status: str = Field(
        ..., description="'MATCHES_FOUND' or 'INSUFFICIENT_INFORMATION'"
    )
    message: str = Field(..., description="Human-readable status summary")
    disclaimer: str = Field(..., description="Mandatory educational prototype disclaimer")
    nutrient_scores: List[NutrientScore] = Field(
        default_factory=list, description="Ranked nutrient groups with Reference match % and risk bands"
    )
    matched_entries: List[MatchedEntry] = Field(
        default_factory=list, description="Ordered reference-match summaries (retained for why details)"
    )
    unmatched_user_tags: List[str] = Field(
        default_factory=list, description="Tags submitted by user that did not match this set"
    )
    package_version: str = Field(..., description="Reference dataset package version")
    matcher_version: str = Field(..., description="Matcher algorithm specification version")
