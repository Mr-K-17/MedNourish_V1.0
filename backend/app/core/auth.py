"""Authentication and Authorization services for Firebase Auth Emulator.

Validates bearer tokens and enforces user identity verification.
Strictly adheres to SEC-01, SEC-02, and SEC-04 (no sensitive data logged).
"""

import json
import logging
import urllib.error
import urllib.request
from typing import Any, Dict, Optional
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.core.config import settings

logger = logging.getLogger(__name__)

security_scheme = HTTPBearer(auto_error=False)


class AuthenticatedUser:
    """Represents a verified user authenticated through the Firebase Auth Emulator."""

    def __init__(self, uid: str, email: Optional[str] = None):
        self.uid = uid
        self.email = email

    def __repr__(self) -> str:
        return f"<AuthenticatedUser uid={self.uid}>"


def verify_firebase_id_token(id_token: str) -> Dict[str, Any]:
    """Verifies a Firebase ID token against the local Auth Emulator.

    Does not trust unsigned client tokens. Calls the emulator's token lookup endpoint.
    """
    if not id_token or not id_token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Clean potential whitespace
    id_token = id_token.strip()

    # Query the Firebase Auth Emulator accounts:lookup endpoint
    emulator_url = f"http://{settings.FIREBASE_AUTH_EMULATOR_HOST}/identitytoolkit.googleapis.com/v1/accounts:lookup?key=fake-api-key"
    payload = json.dumps({"idToken": id_token}).encode("utf-8")

    req = urllib.request.Request(
        emulator_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=3.0) as response:
            data = json.loads(response.read().decode("utf-8"))
            users = data.get("users", [])
            if not users:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired authentication token.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            user_info = users[0]
            return {
                "uid": user_info["localId"],
                "email": user_info.get("email"),
            }
    except urllib.error.HTTPError as exc:
        # Emulator returns 400 for INVALID_ID_TOKEN or TOKEN_EXPIRED
        logger.info("Firebase token verification rejected by emulator.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or revoked authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as exc:
        logger.error("Error communicating with Firebase Auth Emulator: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication verification service is currently unreachable.",
        )


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
) -> AuthenticatedUser:
    """Dependency that extracts and validates the bearer token, returning the AuthenticatedUser."""
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = verify_firebase_id_token(credentials.credentials)
    return AuthenticatedUser(uid=token_data["uid"], email=token_data.get("email"))
