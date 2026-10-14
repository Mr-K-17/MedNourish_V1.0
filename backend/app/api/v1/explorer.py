"""Symptom Reference Explorer API endpoints.

Implements M1B.2:
- GET /v1/explorer/categories: browse available body regions and symptom tags
- POST /v1/explorer/match: submit query tags and receive ordered reference match summary
Adheres to:
- SAF-01, SAF-05, SAF-06, SAF-07, SAF-09, SAF-10, SAF-16, SAF-17
- C-01, C-08, C-18, C-21
- Preserves authentication and adult consent gating
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.auth import AuthenticatedUser, get_current_user
from app.schemas.explorer import CategoriesResponse, MatchRequest, MatchResponse, TagItem
from app.services.knowledge_service import (
    MATCHER_VERSION,
    PACKAGE_VERSION,
    knowledge_repo,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/explorer/categories", response_model=CategoriesResponse)
def get_explorer_categories(
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Retrieves available anatomical regions and symptom tags for exploration.

    Requires authenticated user session.
    """
    tags_by_region = {
        reg: [TagItem(tag=item["tag"], label=item["label"]) for item in tag_list]
        for reg, tag_list in knowledge_repo.tags_by_region.items()
    }
    total_tags = sum(len(tag_list) for tag_list in tags_by_region.values())

    return CategoriesResponse(
        regions=list(tags_by_region.keys()),
        tags_by_region=tags_by_region,
        total_tags=total_tags,
        package_version=PACKAGE_VERSION,
    )


@router.post("/explorer/match", response_model=MatchResponse)
def match_reference_symptoms(
    request: MatchRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Executes deterministic reference matching against curated tables.

    Requires authenticated user session.
    Outputs ordered reference-match summaries or insufficient information state.
    """
    try:
        from app.services.scoring_service import scoring_service
        result = scoring_service.evaluate_tags(
            user_tags=request.selected_tags,
            region_filter=request.body_region_filter,
        )
        return MatchResponse(**result)
    except Exception as exc:
        logger.error("Error executing reference matcher: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing reference match query.",
        )
