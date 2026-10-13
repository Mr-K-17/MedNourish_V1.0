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
from app.schemas.nursebot import HelpMenuResponse, HelpTopicDetail
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
