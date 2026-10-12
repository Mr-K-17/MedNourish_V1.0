"""Schemas for Symptom Reference Explorer API.

Adheres strictly to:
- SAF-01, SAF-07: Educational prototype disclaimers
- SAF-06: Insufficient Information states
- SAF-17: Reference match counts, no diagnostic or predictive scores
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
    review_status: str = Field(
        "unreviewed draft", description="Clinical review status per PV-17 / SAF-13"
    )


class MatchResponse(BaseModel):
    status: str = Field(
        ..., description="'MATCHES_FOUND' or 'INSUFFICIENT_INFORMATION'"
    )
    message: str = Field(..., description="Human-readable status summary")
    disclaimer: str = Field(..., description="Mandatory educational prototype disclaimer")
    matched_entries: List[MatchedEntry] = Field(
        default_factory=list, description="Ordered reference-match summaries"
    )
    unmatched_user_tags: List[str] = Field(
        default_factory=list, description="Tags submitted by user that did not match this set"
    )
    package_version: str = Field(..., description="Reference dataset package version")
    matcher_version: str = Field(..., description="Matcher algorithm specification version")
