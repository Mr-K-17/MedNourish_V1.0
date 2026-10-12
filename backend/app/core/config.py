"""MEDNOURISH Application Configuration.

Strictly follows C-14 (local emulator development) and Architecture.md.
"""

from pydantic import BaseModel


class Settings(BaseModel):
    """Application settings for local Phase 1 development."""

    PROJECT_NAME: str = "MEDNOURISH"
    VERSION: str = "0.1.0-alpha"
    API_V1_STR: str = "/v1"
    ENVIRONMENT: str = "local_emulator"

    # Firebase Emulator Configuration
    FIREBASE_AUTH_EMULATOR_HOST: str = "127.0.0.1:9099"
    FIRESTORE_EMULATOR_HOST: str = "127.0.0.1:8080"

    # Safety Notice
    EDUCATIONAL_PROTOTYPE_DISCLAIMER: str = (
        "MEDNOURISH is an educational prototype. Results are reference-table "
        "matches and general health education, not medical diagnoses or predictions. "
        "Always consult a qualified healthcare professional."
    )


settings = Settings()
