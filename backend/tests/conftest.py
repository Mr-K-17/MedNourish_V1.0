"""Shared Pytest configuration and isolated SQLite test fixtures.

Provides:
- Shared in-memory SQLite engine using StaticPool
- Shared get_db dependency override for test isolation
- autouse fixture to reset tables and dependency overrides between tests
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.auth import get_current_user
from app.core.config import settings
from app.db.session import Base, get_db
from app.main import app
from app.models.user import UserProfile, UserConsentLog, SavedSummary, CarePlanItem, MedScanSession

# Shared test database engine: SQLite in-memory or dedicated MySQL test database
if settings.DB_MODE == "mysql":
    test_engine = create_engine(
        settings.mysql_test_connection_url,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    assert test_engine.url.database.endswith("_test"), (
        "Safety guard: MySQL test runner must only target a database ending with '_test'"
    )
else:
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
Base.metadata.create_all(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Ensure FastAPI uses the isolated test DB
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_test_state():
    """Drops and recreates all tables, and clears user auth overrides."""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_current_user, None)
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
