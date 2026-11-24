# Code Excerpt: `safety_claims_scanner`

- **Repository Path**: [`backend/scripts/scan_safety_claims.py`](file:///C:\Users\USER\Desktop\MedNourish-Dev/backend/scripts/scan_safety_claims.py#L1-L32)
- **Lines**: 1–32 (32 lines)
- **Component**: MEDNOURISH Core Implementation

### Architectural Purpose & Design Rationale
Automated AST and regex auditing script that inspects project files for prohibited medical claims ('diagnoses', 'prescribes', 'cures') and verifies mandatory non-diagnostic disclaimer compliance.

```python
"""MedNourish — Automated Safety & Prohibited Claims Scanner
============================================================
Module: backend.scripts.scan_safety_claims
Spec: Final Finish F6 / SAF-01..SAF-17

Scans frontend code, backend endpoints, seed data, model cards, demo scripts,
and documentation to verify that no affirmative diagnostic, prescriptive, or
clinical probability claims exist in the user-facing application.

Uses an allowlist context check to permit necessary disclaimer, refusal, and
anti-diagnostic documentation sentences (e.g. 'not a medical diagnosis').
"""

import os
import re
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

SCAN_TARGETS = [
    os.path.join(REPO_ROOT, "backend", "app"),
    os.path.join(REPO_ROOT, "backend", "scripts"),
    os.path.join(REPO_ROOT, "frontend", "src"),
    os.path.join(REPO_ROOT, "ml", "artifacts", "vision"),
    os.path.join(REPO_ROOT, "ml", "artifacts", "tabular"),
    os.path.join(REPO_ROOT, "README.md"),
    os.path.join(REPO_ROOT, "docs", "DEMO_SCRIPT.md"),
]

BANNED_PATTERNS = [
    (r"\bautonomous diagnosis\b", "autonomous diagnosis"),
    (r"\bclinical decision support system\b", "clinical decision support system"),
```

> **Educational Prototype Notice**: MEDNOURISH is an academic research prototype and is not certified as a medical device. Code logic produces nutritional deficiency risk estimates for dietary awareness only.
