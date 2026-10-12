"""Tests for public health and root endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.anyio
async def test_root_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "MEDNOURISH"
    assert "educational prototype" in data["disclaimer"].lower()


@pytest.mark.anyio
async def test_health_check_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert data["environment"] in ("local_emulator", "local_development")
    assert "educational prototype" in data["disclaimer"].lower()
    assert "services" in data
    assert "mysql" in data["services"]
    assert "mongodb" in data["services"]
    assert "firebase_auth_emulator" in data["services"]
