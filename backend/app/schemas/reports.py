"""Schemas for Saved Summaries and Reports API.

Implements M1B.3:
- Saving reference-match summaries
- Listing user's saved summaries
- Retrieving single saved summary detail
- Deleting saved summary
Strictly adheres to:
- REPORT-01: Nutritional reference match summary only, no probability or risk scores
- REPORT-04: Records package_version and matcher_version
- SAFE-01, SAF-07: Records educational disclaimer and review status
- PROF-02: User ownership derived from authenticated token
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.explorer import MatchedEntry


class SaveSummaryRequest(BaseModel):
    session_type: str = Field(
        "Explorer", description="Source session type: 'Explorer' or 'MedBot'"
    )
    body_region_filter: Optional[str] = Field(
        None, description="Optional body region filter applied during session"
    )
    selected_tags: List[str] = Field(
        ..., min_length=1, description="List of user symptom tags that were queried"
    )
    matched_entries: List[MatchedEntry] = Field(
        ..., description="List of educational reference match records"
    )
    package_version: str = Field(
        ..., description="Curated dataset reference package version"
    )
    matcher_version: str = Field(
        ..., description="Deterministic matcher specification version"
    )


class SavedSummaryItem(BaseModel):
    id: str = Field(..., description="Unique saved summary identifier")
    session_type: str = Field(..., description="'Explorer' or 'MedBot'")
    body_region_filter: Optional[str] = None
    selected_tags: List[str] = Field(..., description="Selected symptom tags")
    match_count_total: int = Field(
        ..., description="Total reference classes matched"
    )
    top_deficiency_associations: List[str] = Field(
        default_factory=list, description="Top deficiency reference labels"
    )
    package_version: str = Field(..., description="Package version")
    matcher_version: str = Field(..., description="Matcher version")
    review_status: str = Field(..., description="Clinical review status")
    created_at: datetime = Field(..., description="Timestamp of record creation")


class SavedSummaryDetail(SavedSummaryItem):
    matched_entries: List[MatchedEntry] = Field(
        ..., description="Full list of matched reference entries with matched tags"
    )
    disclaimer: str = Field(
        ..., description="Mandatory educational prototype disclaimer"
    )


class SavedSummariesListResponse(BaseModel):
    summaries: List[SavedSummaryItem] = Field(
        default_factory=list, description="List of saved summaries for current user"
    )
    total_count: int = Field(..., description="Total count of saved records")


class DeleteSummaryResponse(BaseModel):
    status: str = Field(..., description="'deleted'")
    id: str = Field(..., description="ID of deleted record")
    message: str = Field(..., description="Success message")
