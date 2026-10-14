"""Comprehensive tests for M1A.4, M1A.5, and M1A.6.

Tests:
1. Authentication verification against Firebase Auth Emulator
2. Rejection of unauthenticated requests (missing/invalid tokens)
3. Profile creation requiring mandatory adult confirmation (18+)
4. Profile rejection when adult confirmation is False
5. Absence of date-of-birth or age fields
6. Data isolation (User A cannot read/write User B data)
7. Minimal profile retrieval and update
8. Account deletion and data removal
"""

import json
import urllib.request
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.auth import get_current_user, AuthenticatedUser
from app.db.session import Base, get_db
from app.main import app

from tests.conftest import TestingSessionLocal, override_get_db


@pytest.mark.anyio
async def test_unauthenticated_profile_access():
    """Unauthenticated requests must be rejected with 401 Unauthorized (SEC-01)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/v1/profile")
    assert response.status_code == 401
    assert "detail" in response.json()


@pytest.mark.anyio
async def test_invalid_token_rejected():
    """Invalid bearer tokens must be rejected with 401 Unauthorized or 503 if emulator is offline."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/v1/profile",
            headers={"Authorization": "Bearer invalid_garbage_token"},
        )
    # 401 if emulator is reachable and rejects token; 503 if emulator is offline
    assert response.status_code in (401, 503)


@pytest.mark.anyio
async def test_adult_confirmation_required():
    """Profile creation must strictly require adult confirmation (SAF-10, C-01)."""
    # Override current user dependency with mock authenticated user
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        uid="test_user_adult_check", email="adult@example.com"
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Attempt with is_adult_confirmed=False
        res_fail = await client.post(
            "/v1/profile",
            json={
                "is_adult_confirmed": False,
                "terms_consent_version": "v1.0",
                "display_name": "Test User",
            },
        )
        assert res_fail.status_code == 422  # Validation error

        # 2. Succeed with is_adult_confirmed=True
        res_success = await client.post(
            "/v1/profile",
            json={
                "is_adult_confirmed": True,
                "terms_consent_version": "v1.0",
                "display_name": "Adult User",
                "gender": "prefer_not_to_say",
                "height_cm": 175.0,
                "weight_kg": 70.0,
            },
        )
        assert res_success.status_code == 201
        data = res_success.json()
        assert data["id"] == "test_user_adult_check"
        assert data["is_adult_confirmed"] is True
        assert data["terms_consent_version"] == "v1.0"
        # Verify NO DOB or date_of_birth fields exist in response (C-21, C-33)
        assert "dob" not in data
        assert "date_of_birth" not in data


@pytest.mark.anyio
async def test_user_data_isolation():
    """User A cannot access or overwrite User B's profile (SEC-02, PROF-02)."""
    transport = ASGITransport(app=app)

    # 1. User A creates profile
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(uid="user_A")
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/v1/profile",
            json={
                "is_adult_confirmed": True,
                "terms_consent_version": "v1.0",
                "display_name": "Alice",
            },
        )
        assert res.status_code == 201

    # 2. User B requests profile -> gets 404 (their own profile does not exist)
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(uid="user_B")
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_b = await client.get("/v1/profile")
        assert res_b.status_code == 404

    # 3. User A requests profile -> gets Alice
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(uid="user_A")
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res_a = await client.get("/v1/profile")
        assert res_a.status_code == 200
        assert res_a.json()["display_name"] == "Alice"


@pytest.mark.anyio
async def test_profile_update_and_account_deletion():
    """Profile fields can be updated, and account deletion deletes user data (AUTH-05, PROF-03)."""
    transport = ASGITransport(app=app)
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(uid="user_delete_test")

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create
        await client.post(
            "/v1/profile",
            json={
                "is_adult_confirmed": True,
                "terms_consent_version": "v1.0",
                "display_name": "Initial Name",
            },
        )

        # Update optional field
        res_update = await client.put(
            "/v1/profile",
            json={"display_name": "Updated Name", "height_cm": 180.0},
        )
        assert res_update.status_code == 200
        assert res_update.json()["display_name"] == "Updated Name"
        assert res_update.json()["height_cm"] == 180.0

        # Delete account
        res_del = await client.delete("/v1/profile")
        assert res_del.status_code == 200
        assert res_del.json()["status"] == "deleted"

        # Verify profile is now gone
        res_verify = await client.get("/v1/profile")
        assert res_verify.status_code == 404


@pytest.mark.anyio
async def test_live_emulator_token_integration():
    """End-to-end integration test with live Firebase Auth Emulator."""
    import time
    import socket

    # Check whether emulator port 9099 is actively listening
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        if s.connect_ex(("127.0.0.1", 9099)) != 0:
            pytest.skip("Firebase Auth Emulator is not currently running on port 9099 (stopped per Task 0).")

    unique_email = f"e2e_{int(time.time() * 1000)}@example.com"
    # Register fictional user on the emulator to obtain genuine ID token
    req = urllib.request.Request(
        "http://127.0.0.1:9099/identitytoolkit.googleapis.com/v1/accounts:signUp?key=fake-api-key",
        data=json.dumps(
            {
                "email": unique_email,
                "password": "Password123!",
                "returnSecureToken": True,
            }
        ).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        auth_data = json.loads(resp.read().decode("utf-8"))
        id_token = auth_data["idToken"]
        local_id = auth_data["localId"]

    # Remove override to test actual token verification pipeline
    app.dependency_overrides.pop(get_current_user, None)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Post profile with genuine emulator token in header
        res = await client.post(
            "/v1/profile",
            headers={"Authorization": f"Bearer {id_token}"},
            json={
                "is_adult_confirmed": True,
                "terms_consent_version": "v1.0",
                "display_name": "E2E User",
            },
        )
        assert res.status_code == 201
        data = res.json()
        assert data["id"] == local_id
        assert data["display_name"] == "E2E User"
        assert data["is_adult_confirmed"] is True


@pytest.mark.anyio
async def test_database_failure_graceful_handling():
    """Endpoints return 503 Service Unavailable when the database is unreachable."""
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(uid="db_fail_user")

    class FailingSession:
        def query(self, *args, **kwargs):
            raise RuntimeError("Database connection timed out or refused")

    def failing_db():
        yield FailingSession()

    app.dependency_overrides[get_db] = failing_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/v1/profile")
        assert res.status_code == 503
        assert "Database service unavailable" in res.json()["detail"]

    # Restore in-memory db override
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.anyio
async def test_account_deletion_removes_consent_logs_in_dev():
    """Development deletes all records including consent logs upon account deletion per OD-08 and M1A.6."""
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(uid="consent_log_del_user")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create profile and consent log
        await client.post(
            "/v1/profile",
            json={
                "is_adult_confirmed": True,
                "terms_consent_version": "v1.0",
                "display_name": "Consent User",
            },
        )

        # Delete account
        del_res = await client.delete("/v1/profile")
        assert del_res.status_code == 200

        # Verify DB directly: consent logs must be removed
        db = TestingSessionLocal()
        from app.models.user import UserConsentLog, UserProfile

        consent_count = db.query(UserConsentLog).filter(UserConsentLog.user_id == "consent_log_del_user").count()
        profile_count = db.query(UserProfile).filter(UserProfile.id == "consent_log_del_user").count()
        db.close()

        assert consent_count == 0
        assert profile_count == 0

    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.anyio
async def test_v2_profile_extensions_c33():
    """Test C-33 profile extensions: age (1-120), under-18 notice, blood_type, conditions, other_condition."""
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(uid="user_c33_test")
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Invalid age (> 120)
        res = await client.post(
            "/v1/profile",
            json={
                "demo_consent_confirmed": True,
                "terms_consent_version": "v1.0",
                "age": 125,
            },
        )
        assert res.status_code == 422

        # 2. Invalid blood type
        res = await client.post(
            "/v1/profile",
            json={
                "demo_consent_confirmed": True,
                "terms_consent_version": "v1.0",
                "blood_type": "Z+",
            },
        )
        assert res.status_code == 422

        # 3. Invalid condition
        res = await client.post(
            "/v1/profile",
            json={
                "demo_consent_confirmed": True,
                "terms_consent_version": "v1.0",
                "conditions": ["NonexistentDisease123"],
            },
        )
        assert res.status_code == 422

        # 4. Valid under-18 user with demo consent
        res = await client.post(
            "/v1/profile",
            json={
                "demo_consent_confirmed": True,
                "terms_consent_version": "v1.0",
                "display_name": "Teen User",
                "age": 16,
                "blood_type": "B+",
                "conditions": ["Anemia", "Asthma"],
                "other_condition": "Seasonal rhinitis",
            },
        )
        assert res.status_code == 201
        data = res.json()
        assert data["age"] == 16
        assert data["blood_type"] == "B+"
        assert set(data["conditions"]) == {"Anemia", "Asthma"}
        assert data["other_condition"] == "Seasonal rhinitis"
        assert data["under_18_notice"] == "Reference content is written for adults; demo only."
        assert "dob" not in data
        assert "date_of_birth" not in data

        # 5. Update profile to age 25 -> under_18_notice becomes None
        res_update = await client.put(
            "/v1/profile",
            json={
                "age": 25,
                "conditions": ["Anemia"],
            },
        )
        assert res_update.status_code == 200
        up_data = res_update.json()
        assert up_data["age"] == 25
        assert up_data["conditions"] == ["Anemia"]
        assert up_data["under_18_notice"] is None

        # Clean up
        await client.delete("/v1/profile")

    app.dependency_overrides.pop(get_current_user, None)


