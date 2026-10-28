"""MEDNOURISH Application Configuration.

Loads configuration from environment variables with fallback defaults for local development.
Never hardcodes secrets.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel


def _load_env_file() -> None:
    """Safely loads variables from local .env into os.environ if present.

    Does not overwrite already-set environment variables.
    Never exposes or logs values.
    """
    # Check current directory, repo root, and backend root
    candidates = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parents[2] / ".env",
        Path(__file__).resolve().parents[3] / ".env",
    ]
    for env_path in candidates:
        if env_path.is_file():
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        key, val = line.split("=", 1)
                        key = key.strip()
                        val = val.strip()
                        # Strip surrounding single or double quotes
                        if len(val) >= 2 and (
                            (val.startswith('"') and val.endswith('"'))
                            or (val.startswith("'") and val.endswith("'"))
                        ):
                            val = val[1:-1]
                        if key and key not in os.environ:
                            os.environ[key] = val
            except Exception:
                pass
            break


_load_env_file()


class Settings(BaseModel):
    """Application settings for local Phase 1 development."""

    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "MEDNOURISH")
    VERSION: str = os.getenv("VERSION", "0.1.0-alpha")
    API_V1_STR: str = "/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "local_development")

    # Firebase Auth Emulator Configuration
    FIREBASE_AUTH_EMULATOR_HOST: str = os.getenv("FIREBASE_AUTH_EMULATOR_HOST", "127.0.0.1:9099")
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "demo-mednourish")

    # Database Mode Toggle: 'sqlite' (default fallback) or 'mysql'
    DB_MODE: str = os.getenv("DB_MODE", "sqlite").lower()

    # MySQL Configuration (Primary structured relational storage)
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "mednourish_dev")

    # MongoDB Configuration (Optional document store; reference knowledge is loaded from curated CSVs)
    MONGO_URL: Optional[str] = os.getenv("MONGO_URL") or os.getenv("MONGODB_URI")
    MONGODB_URI: Optional[str] = os.getenv("MONGO_URL") or os.getenv("MONGODB_URI")
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "mednourish_reference")

    # Safety Notice
    EDUCATIONAL_PROTOTYPE_DISCLAIMER: str = (
        "MEDNOURISH is an educational prototype. Results are reference-table "
        "matches and general health education, not medical diagnoses or predictions. "
        "Always consult a qualified healthcare professional."
    )

    @property
    def sqlite_file_path(self) -> Path:
        """Returns the local SQLite database path."""
        return Path(__file__).resolve().parents[2] / "mednourish_dev.db"

    @property
    def mysql_connection_url(self) -> str:
        """Constructs safe MySQL connection URL for SQLAlchemy."""
        pwd = f":{self.MYSQL_PASSWORD}" if self.MYSQL_PASSWORD else ""
        return f"mysql+pymysql://{self.MYSQL_USER}{pwd}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"

    @property
    def mysql_test_connection_url(self) -> str:
        """Constructs safe MySQL connection URL for isolated test execution on mednourish_test."""
        pwd = f":{self.MYSQL_PASSWORD}" if self.MYSQL_PASSWORD else ""
        return f"mysql+pymysql://{self.MYSQL_USER}{pwd}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/mednourish_test"

    @property
    def database_url(self) -> str:
        """Returns active database connection URL based on DB_MODE."""
        if self.DB_MODE == "mysql":
            return self.mysql_connection_url
        return f"sqlite:///{self.sqlite_file_path.as_posix()}"


settings = Settings()
