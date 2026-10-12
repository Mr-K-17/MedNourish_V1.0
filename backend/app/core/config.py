"""MEDNOURISH Application Configuration.

Loads configuration from environment variables with fallback defaults for local development.
Never hardcodes secrets.
"""

import os
from pydantic import BaseModel


class Settings(BaseModel):
    """Application settings for local Phase 1 development."""

    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "MEDNOURISH")
    VERSION: str = os.getenv("VERSION", "0.1.0-alpha")
    API_V1_STR: str = "/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "local_development")

    # Firebase Auth Emulator Configuration
    FIREBASE_AUTH_EMULATOR_HOST: str = os.getenv("FIREBASE_AUTH_EMULATOR_HOST", "127.0.0.1:9099")
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "demo-mednourish")

    # MySQL Configuration (Primary structured relational storage)
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "mednourish_dev")

    # MongoDB Configuration (Versioned document reference content)
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
    MONGODB_DATABASE: str = os.getenv("MONGODB_DATABASE", "mednourish_reference")

    # Safety Notice
    EDUCATIONAL_PROTOTYPE_DISCLAIMER: str = (
        "MEDNOURISH is an educational prototype. Results are reference-table "
        "matches and general health education, not medical diagnoses or predictions. "
        "Always consult a qualified healthcare professional."
    )

    @property
    def mysql_connection_url(self) -> str:
        """Constructs safe MySQL connection URL for SQLAlchemy."""
        pwd = f":{self.MYSQL_PASSWORD}" if self.MYSQL_PASSWORD else ""
        return f"mysql+pymysql://{self.MYSQL_USER}{pwd}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"


settings = Settings()
