"""Database connections management for MySQL and MongoDB.

Provides resilient connection checks without exposing credentials.
"""

import logging
from typing import Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from pymongo import MongoClient
from app.core.config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy Base for MySQL models
Base = declarative_base()

# Database Engine and Session Factory
try:
    if settings.DB_MODE == "mysql":
        engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args={"connect_timeout": 3},
        )
    else:
        engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False},
        )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    logger.warning("Database engine initialization warning: %s", str(e))
    engine = None
    SessionLocal = None


def get_db():
    """Dependency that provides a database session."""
    if SessionLocal is None:
        raise RuntimeError("Database session factory is not configured.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_mysql_health() -> Dict[str, Any]:
    """Tests database connectivity and returns status without leaking credentials."""
    if engine is None:
        return {"status": "unconfigured", "error": "Engine not initialized"}
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            if result == 1:
                if settings.DB_MODE == "mysql":
                    return {"status": "healthy", "engine": "MySQL 8.0", "mode": "mysql"}
                return {"status": "healthy", "engine": "SQLite 3", "mode": "sqlite"}
        return {"status": "unhealthy", "error": "Query returned unexpected result"}
    except Exception as exc:
        # Sanitize error message to avoid credential leaks
        err_type = type(exc).__name__
        err_msg = str(exc)
        if "1045" in err_msg or "Access denied" in err_msg:
            return {"status": "unauthorized", "message": "Authentication required. Verify MYSQL_PASSWORD in .env"}
        elif "Can't connect" in err_msg or "2003" in err_msg:
            return {"status": "offline", "message": "MySQL server is not running on configured host/port"}
        return {"status": "error", "error_type": err_type}


def check_mongodb_health() -> Dict[str, Any]:
    """Tests MongoDB connectivity safely. Reference knowledge is served from CSVs; MongoDB is optional."""
    mongo_uri = settings.MONGO_URL or settings.MONGODB_URI
    if not mongo_uri:
        return {
            "status": "not configured (optional)",
            "service": "MongoDB",
            "message": "Reference knowledge is loaded from curated CSV files; MongoDB document store is optional",
        }
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
        # The ismaster/ping command is cheap and does not require auth on unauthenticated local instances
        client.admin.command("ping")
        return {"status": "healthy", "service": "MongoDB"}
    except Exception as exc:
        return {
            "status": "unavailable",
            "service": "MongoDB",
            "message": f"MongoDB server is unreachable on configured URL: {type(exc).__name__}",
        }
