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


def test_check_mongodb_health_optional(monkeypatch):
    from app.db.session import check_mongodb_health
    from app.core.config import settings

    monkeypatch.setattr(settings, "MONGO_URL", None)
    monkeypatch.setattr(settings, "MONGODB_URI", None)
    result = check_mongodb_health()
    assert result["status"] == "not configured (optional)"
    assert "optional" in result["message"].lower()


def test_check_mongodb_health_unreachable(monkeypatch):
    from app.db.session import check_mongodb_health
    from app.core.config import settings

    monkeypatch.setattr(settings, "MONGO_URL", "mongodb://127.0.0.1:99999")
    monkeypatch.setattr(settings, "MONGODB_URI", "mongodb://127.0.0.1:99999")
    result = check_mongodb_health()
    assert result["status"] == "unavailable"
