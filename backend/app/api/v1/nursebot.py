"""NurseBot Scripted App Help API endpoints.

Implements M1B.6 Scripted app help:
- GET /v1/nursebot/menu: retrieve all available help topics and FAQs
- GET /v1/nursebot/topics/{topic_id}: retrieve scripted content and guidance for a selected topic

Adheres strictly to:
- NURSE-01: Menu-based scripted help and FAQ about using the app.
  No free-text input, no LLM, no stored transcripts (C-15, C-23).
- NURSE-03, NURSE-04, SAF-14: Explicit refusal patterns for diagnosis, medicine, and dosages.
- All writes and transcripts strictly omitted.
- Requires authenticated user session (401 if unauthenticated).
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.auth import AuthenticatedUser, get_current_user
from app.schemas.nursebot import (
    HelpMenuResponse,
    HelpTopicDetail,
    NurseBotAskRequest,
    NurseBotAskResponse,
)
from app.services.nursebot_service import nursebot_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/nursebot/menu", response_model=HelpMenuResponse)
def get_nursebot_menu(
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Retrieves menu of scripted help topics and FAQs.

    Requires authenticated session.
    """
    return nursebot_service.get_menu()


@router.get("/nursebot/topics/{topic_id}", response_model=HelpTopicDetail)
def get_nursebot_topic(
    topic_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Retrieves scripted text for a specific help or refusal topic.

    Requires authenticated session.
    """
    topic = nursebot_service.get_topic_detail(topic_id)
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Help topic '{topic_id}' not found.",
        )
    return topic


@router.post("/nursebot/ask", response_model=NurseBotAskResponse)
async def ask_nursebot(
    payload: NurseBotAskRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Processes user question through the NurseBot intent router.

    - Rate limit: max 10 queries per minute per user.
    - Intent router handles emergency, diagnosis/dosage refusal, app help, and web reference.
    - Zero chat transcripts stored in database or files.
    - Requires authenticated session.
    """
    if not nursebot_service.check_rate_limit(current_user.uid):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Maximum 10 queries per minute.",
        )

    return await nursebot_service.ask(current_user.uid, payload.question)

