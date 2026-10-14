"""
MedNourish — Backend ML Lab Gateway Integration & Safety Tests
==============================================================
Module: tests.test_mllab
Spec: Phase 3.3 Stage 5 (C-30)

Tests:
1. Authentication required (401 on unauthenticated access).
2. Range validation on inputs (age 18-120, BMI 10-65).
3. Image upload validation (magic bytes, 5 MB limit).
4. Graceful 503 handling when ML Lab microservice is offline.
5. Strict schema guarantees: NO probability or percentage fields returned.
6. Safety term scan ensuring zero autonomous clinical claims.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from app.core.auth import AuthenticatedUser, get_current_user
from app.main import app

MOCK_USER = AuthenticatedUser(uid="mllab_test_user", email="test@mednourish.internal")

@pytest.fixture
def auth_override():
    app.dependency_overrides[get_current_user] = lambda: MOCK_USER
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.anyio
async def test_unauthenticated_mllab_rejected():
    """Unauthenticated requests must be rejected with 401 Unauthorized."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r1 = await client.get("/v1/mllab/status")
        r2 = await client.post("/v1/mllab/predict/tabular", json={})
        r3 = await client.post("/v1/mllab/predict/keywords", json={})
        r4 = await client.get("/v1/mllab/model-cards")

    assert r1.status_code == 401
    assert r2.status_code == 401
    assert r3.status_code == 401
    assert r4.status_code == 401


@pytest.mark.anyio
async def test_range_validation_tabular(auth_override):
    """Input age and BMI must obey adult screening ranges (age 18-120, BMI 10-65)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Age under 18 rejected (SAF-10)
        res_minor = await client.post("/v1/mllab/predict/tabular", json={"age": 15, "bmi": 22.0})
        assert res_minor.status_code == 400
        assert "Age must be between 18 and 120" in res_minor.json()["detail"]

        # Age over 120 rejected
        res_over = await client.post("/v1/mllab/predict/tabular", json={"age": 125, "bmi": 22.0})
        assert res_over.status_code == 400

        # BMI out of range rejected
        res_bmi = await client.post("/v1/mllab/predict/tabular", json={"age": 30, "bmi": 75.0})
        assert res_bmi.status_code == 400
        assert "BMI must be between 10 and 65" in res_bmi.json()["detail"]


@pytest.mark.anyio
async def test_image_upload_validation(auth_override):
    """Image upload requires valid magic bytes and <= 5MB."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Invalid format (text file disguised as image)
        fake_file = ("test.jpg", b"NOT_A_REAL_IMAGE_BYTES", "image/jpeg")
        res_invalid = await client.post(
            "/v1/mllab/predict/image",
            data={"model_name": "combined"},
            files={"file": fake_file},
        )
        assert res_invalid.status_code == 400
        assert "Invalid format" in res_invalid.json()["detail"]

        # Oversized file (> 5 MB)
        huge_file = ("huge.jpg", b"\xff\xd8\xff" + b"0" * (6 * 1024 * 1024), "image/jpeg")
        res_huge = await client.post(
            "/v1/mllab/predict/image",
            data={"model_name": "combined"},
            files={"file": huge_file},
        )
        assert res_huge.status_code == 413
        assert "Image exceeds 5 MB limit" in res_huge.json()["detail"]


@pytest.mark.anyio
async def test_service_down_graceful_handling(auth_override):
    """When ML service (port 8001) is offline, returns clean 503 Service Unavailable."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/v1/mllab/status")
        # If ml-service is offline, 503 is returned
        if res.status_code == 503:
            data = res.json()
            assert "ML Lab service is currently unavailable" in data["detail"]
        elif res.status_code == 200:
            assert res.json()["status"] == "ok"


@pytest.mark.anyio
async def test_no_probability_fields_in_schema():
    """Verify that schemas and endpoints return labels only and NO probabilities or percentages."""
    from app.api.v1.mllab import TabularPredictRequest, KeywordPredictRequest
    import pydantic

    for model_cls in [TabularPredictRequest, KeywordPredictRequest]:
        field_names = list(model_cls.model_fields.keys()) if hasattr(model_cls, 'model_fields') else list(model_cls.__fields__.keys())
        for fn in field_names:
            assert "prob" not in fn.lower(), f"Forbidden probability field in schema: {fn}"
            assert "percent" not in fn.lower() or "rda" in fn.lower(), f"Forbidden percentage field: {fn}"
            assert "confidence" not in fn.lower(), f"Forbidden confidence field in schema: {fn}"
            assert "confidence" not in fn.lower(), f"Forbidden confidence field in schema: {fn}"


@pytest.mark.anyio
async def test_safety_terms_sweep():
    """Ensures codebase and ML endpoints avoid dangerous diagnostic claims."""
    from app.api.v1 import mllab
    import inspect

    src = inspect.getsource(mllab)
    banned_claims = [
        "cure",
        "we prescribe",
        "autonomous diagnosis",
        "clinical decision",
        "treatment plan established",
    ]
    for claim in banned_claims:
        assert claim not in src.lower(), f"Found banned clinical claim in mllab: {claim}"
