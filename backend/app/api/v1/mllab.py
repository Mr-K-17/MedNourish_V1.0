"""
MedNourish — Backend ML Lab Gateway & Proxy Router
===================================================
Module: app.api.v1.mllab
Spec: Phase 3.3 Stage 5 (C-30)

Proxies authenticated requests from MedNourish client to the isolated
ML Lab microservice on http://127.0.0.1:8001.

Strict Architectural Guarantees:
- Backend NEVER imports TensorFlow, PyTorch, or large vision libraries.
- Requires authenticated user via get_current_user dependency.
- Handles service-down gracefully with HTTP 503 error.
- Enforces 5 MB file size limit and magic bytes validation.
- Zero persistence: stores NO patient inputs, biomarker values, or uploaded images.
- Zero health logging: logs no patient attributes or predictions.
"""

import io
import logging
from typing import Any, Dict, List, Optional
import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.core.auth import AuthenticatedUser, get_current_user
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

ML_SERVICE_URL = "http://127.0.0.1:8001"
TIMEOUT_SECONDS = 10.0


class TabularPredictRequest(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    bmi: Optional[float] = None
    diet_type: Optional[str] = None
    symptoms: Optional[List[str]] = None
    biomarkers: Optional[Dict[str, float]] = None


class KeywordPredictRequest(BaseModel):
    body_region: str
    keywords: List[str]


# --------------------------------------------------------------------------
# Proxy Helper
# --------------------------------------------------------------------------

async def forward_request(method: str, path: str, json_data: Optional[Dict] = None, files: Optional[Dict] = None, data: Optional[Dict] = None) -> Any:
    url = f"{ML_SERVICE_URL}{path}"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            if method == "GET":
                resp = await client.get(url)
            elif method == "POST":
                if files:
                    resp = await client.post(url, data=data, files=files)
                else:
                    resp = await client.post(url, json=json_data)
            else:
                raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail="Method not allowed")
            
            if resp.status_code >= 400:
                raise HTTPException(status_code=resp.status_code, detail=resp.json().get("detail", resp.text))
            return resp.json()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML Lab service is currently unavailable. Start ml-service on port 8001.",
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="ML Lab service request timed out.",
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error connecting to ML Lab service: {str(e)}",
        )


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------

@router.get("/mllab/status")
async def get_mllab_status(
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Checks availability of the ML Lab microservice."""
    return await forward_request("GET", "/health")


@router.post("/mllab/predict/tabular")
async def proxy_predict_tabular(
    payload: Dict[str, Any],
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Proxies tabular prediction to ML Lab service. Returns labels only (no percentages)."""
    # Range validation
    age = payload.get("age")
    if age is not None and (age < 18 or age > 120):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Age must be between 18 and 120")

    bmi = payload.get("bmi")
    if bmi is not None and (bmi < 10 or bmi > 65):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="BMI must be between 10 and 65")

    return await forward_request("POST", "/predict/tabular", json_data=payload)


@router.post("/mllab/predict/keywords")
async def proxy_predict_keywords(
    payload: Dict[str, Any],
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Proxies keyword ranking to ML Lab service."""
    if not payload.get("keywords") or not payload.get("body_region"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="body_region and keywords are required")
    if isinstance(payload.get("keywords"), list):
        payload["keywords"] = ", ".join(payload["keywords"])
    return await forward_request("POST", "/predict/keywords", json_data=payload)


@router.post("/mllab/predict/image")
async def proxy_predict_image(
    model_name: str = Form(...),
    file: UploadFile = File(...),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Validates image and proxies to ML Lab service. Returns top-3 classes only (no percentages)."""
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Image exceeds 5 MB limit")

    # Magic bytes check
    if not (contents.startswith(b"\xff\xd8\xff") or contents.startswith(b"\x89PNG") or contents.startswith(b"RIFF")):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid format. Allowed: JPEG, PNG, WEBP")

    files = {"file": (file.filename, contents, file.content_type)}
    data = {"model_name": model_name}
    return await forward_request("POST", "/predict/image", files=files, data=data)


@router.get("/mllab/model-cards")
async def proxy_get_model_cards(
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Returns catalog of model cards."""
    return await forward_request("GET", "/model-cards")


@router.get("/mllab/model-cards/{card_id}")
async def proxy_get_model_card_detail(
    card_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Returns detailed model card metrics and confusion matrix."""
    return await forward_request("GET", f"/model-cards/{card_id}")
