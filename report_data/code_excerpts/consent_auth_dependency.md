# Code Excerpt: `consent_auth_dependency`

- **Repository Path**: [`backend/app/core/auth.py`](file:///C:\Users\USER\Desktop\MedNourish-Dev/backend/app/core/auth.py#L1-L30)
- **Lines**: 1–30 (30 lines)
- **Component**: MEDNOURISH Core Implementation

### Architectural Purpose & Design Rationale
FastAPI dependency intercepting incoming requests to verify valid Bearer JWT authentication and check database consent logs, returning HTTP 403 Forbidden if user consent has not been recorded.

```python
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
```

> **Educational Prototype Notice**: MEDNOURISH is an academic research prototype and is not certified as a medical device. Code logic produces nutritional deficiency risk estimates for dietary awareness only.
