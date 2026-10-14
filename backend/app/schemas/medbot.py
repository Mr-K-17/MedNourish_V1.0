"""Questionnaire models and schemas for MedBot (M1B.4).

Adheres strictly to:
- MEDBOT-01: Approved questionnaire inputs in Simple or Standard mode.
- MEDBOT-02: Interaction modes Simple (yes/no) and Standard (multiple choice).
- MEDBOT-03: Deterministic reference matching using approved symptom tags.
- MEDBOT-04: Reference match summary output only with educational disclaimer.
- MEDBOT-05: No medicine, supplement, dose or treatment text.
- MEDBOT-06: Question skip, back, resume, and cancellation support.
- MEDBOT-10: Lifestyle questions optional, consented, and never alter results.
- SAF-01, SAF-03, SAF-06, SAF-07, SAF-17: Educational prototype constraints.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.explorer import MatchedEntry, NutrientScore


class SymptomChip(BaseModel):
    tag: str = Field(..., description="Canonical symptom tag")
    source_phrase: str = Field(..., description="Matched phrase from user input")
    confidence: float = Field(..., description="Match confidence or similarity score")


class MedBotExtractRequest(BaseModel):
    text: str = Field(..., description="User free-text symptom description")


class MedBotExtractResponse(BaseModel):
    status: str = Field(..., description="'SYMPTOMS_EXTRACTED' or 'INSUFFICIENT_INFORMATION'")
    message: str = Field(..., description="Status summary")
    tags: List[str] = Field(default_factory=list, description="Unique canonical symptom tags extracted")
    chips: List[SymptomChip] = Field(default_factory=list, description="Extracted chips with source phrases")


class QuestionOption(BaseModel):
    id: str = Field(..., description="Unique option identifier within question")
    label: str = Field(..., description="User-facing plain-language label")
    tag: Optional[str] = Field(
        None, description="Associated normalized symptom tag if applicable (null for 'no'/'skip' or lifestyle options)"
    )
    is_none_or_no: bool = Field(
        False, description="True if option explicitly denies symptom (e.g. 'No' or 'None of the above')"
    )


class QuestionnaireQuestion(BaseModel):
    id: str = Field(..., description="Unique stable question identifier")
    step_number: int = Field(..., description="1-indexed sequence number")
    body_region: str = Field(..., description="Anatomical body region (EYES, HAIR, LIPS, NAILS, SKIN, TONGUE, GENERAL)")
    question_text: str = Field(..., description="Clear, plain-language question prompt")
    explanation: Optional[str] = Field(None, description="Plain-language reason why this question is asked")
    mode_availability: List[str] = Field(
        default_factory=lambda: ["simple", "standard"],
        description="Supported modes for this question ('simple', 'standard', or both)",
    )
    is_optional: bool = Field(True, description="Whether user can skip this question")
    is_lifestyle: bool = Field(False, description="True for lifestyle/dietary context questions that NEVER alter matcher results")
    allow_multiple: bool = Field(False, description="True if multiple options can be chosen (Standard mode)")
    options: List[QuestionOption] = Field(default_factory=list, description="Selectable options")


class QuestionnaireConfigResponse(BaseModel):
    mode: str = Field(..., description="Requested questionnaire mode ('simple' or 'standard')")
    total_steps: int = Field(..., description="Total number of steps in this mode")
    disclaimer: str = Field(..., description="Mandatory educational prototype disclaimer")
    questions: List[QuestionnaireQuestion] = Field(..., description="Ordered list of questionnaire questions")
    package_version: str = Field(..., description="Curated reference package version")
    matcher_version: str = Field(..., description="Matcher specification version")


class AnswerSubmission(BaseModel):
    question_id: str = Field(..., description="Target question identifier")
    selected_option_ids: List[str] = Field(default_factory=list, description="IDs of chosen options")
    skipped: bool = Field(False, description="True if user explicitly skipped the step")


class MedBotEvaluateRequest(BaseModel):
    mode: str = Field(..., description="'simple' or 'standard'")
    answers: List[AnswerSubmission] = Field(default_factory=list, description="List of submitted answers across steps")
    confirmed_free_text_tags: Optional[List[str]] = Field(
        default_factory=list, description="Confirmed symptom tags from free-text extraction (Phase 2)"
    )


class MedBotEvaluateResponse(BaseModel):
    status: str = Field(..., description="'MATCHES_FOUND' or 'INSUFFICIENT_INFORMATION'")
    message: str = Field(..., description="Human-readable outcome summary")
    disclaimer: str = Field(..., description="Educational prototype disclaimer")
    collected_symptom_tags: List[str] = Field(default_factory=list, description="Normalized symptom tags derived from answers")
    lifestyle_responses: dict[str, List[str]] = Field(
        default_factory=dict, description="Lifestyle answers recorded for context (verified non-influencing)"
    )
    nutrient_scores: List[NutrientScore] = Field(
        default_factory=list, description="Ranked nutrient groups with Reference match % and risk bands"
    )
    matched_entries: List[MatchedEntry] = Field(
        default_factory=list, description="Ordered reference-match summaries (retained for why details)"
    )
    unmatched_user_tags: List[str] = Field(
        default_factory=list, description="Symptom tags that found no condition match"
    )
    package_version: str = Field(..., description="Curated reference package version")
    matcher_version: str = Field(..., description="Matcher specification version")
    review_status: str = Field("unreviewed draft", description="Clinical review status")
