"""Schemas for Scripted App Help / NurseBot (M1B.6).

Adheres strictly to:
- NURSE-01: Scripted app help and FAQ about using the application.
  No free-text input, no LLM, no stored transcripts (C-15, C-23).
- NURSE-03, NURSE-04, SAF-14: Explicit refusal and redirection patterns for
  diagnosis, medicine, supplement, dosage, or out-of-scope medical requests.
- SAFE-01, SAF-07: Educational prototype disclaimer.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class HelpTopicSummary(BaseModel):
    id: str = Field(..., description="Unique stable topic identifier")
    category: str = Field(..., description="Category: 'app_usage', 'privacy_consent', 'educational_scope', 'safety_refusals'")
    title: str = Field(..., description="Topic title / menu label")
    summary: str = Field(..., description="Brief one-line topic summary")
    is_safety_refusal: bool = Field(False, description="True if topic represents a scripted safety refusal pattern")


class HelpTopicDetail(HelpTopicSummary):
    content: str = Field(..., description="Scripted educational or procedural text")
    related_actions: Optional[List[str]] = Field(default_factory=list, description="Suggested navigational links (e.g. 'Open Dashboard', 'Emergency Help')")
    disclaimer: str = Field(
        "MEDNOURISH NurseBot is a scripted application guide. It is not a real nurse or healthcare professional and cannot diagnose conditions or prescribe medications.",
        description="Mandatory prototype limitation disclaimer",
    )


class HelpMenuResponse(BaseModel):
    categories: List[str] = Field(..., description="Available help topic categories")
    topics: List[HelpTopicSummary] = Field(..., description="List of scripted help topics")
    disclaimer: str = Field(
        "MEDNOURISH NurseBot provides scripted help for using the app. It does not provide medical advice or diagnoses.",
        description="Menu-level prototype disclaimer",
    )
