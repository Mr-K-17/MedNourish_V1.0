# Code Excerpt: `careplan_ics_export`

- **Repository Path**: [`backend/app/services/careplan_sync_service.py`](file:///C:\Users\USER\Desktop\MedNourish-Dev/backend/app/services/careplan_sync_service.py#L1-L32)
- **Lines**: 1–32 (32 lines)
- **Component**: MEDNOURISH Core Implementation

### Architectural Purpose & Design Rationale
Serializes daily nutrition, hydration, and lifestyle checklists into standard RFC 5545 iCalendar (.ics) format with VEVENT, UID, DTSTAMP, and RRULE for live sync with external calendar clients.

```python
"""CarePlan Auto-Sync Service from Assessment Reports (Phase 5).

Guarantees:
- Syncs top 2 nutrients with percentage >= 30 into actionable wellness routines.
- Strictly uses curated non-medication columns: Dietary_Recommendations, Lifestyle_Routine, Follow_Up_Recommendation.
- STRICTLY EXCLUDES Suggested_Supplementation and drug/dosage terms.
- Strips timeframes and medication terms.
- Flagged auto=True with source_entry_id and de-duplicated by (nutrient, text_hash).
- Marks items stale when nutrient falls below 30.
- NEVER deletes user-created (auto=False) or user-edited (is_user_edited=True) items.
- High risk band automatically adds a 'consult a qualified clinician' item.
"""

import csv
import hashlib
import logging
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.user import CarePlanItem

logger = logging.getLogger(__name__)

CURATED_ROUTINE_DIR = Path("knowledge/curated")


def clean_routine_text(raw_text: str) -> str:
```

> **Educational Prototype Notice**: MEDNOURISH is an academic research prototype and is not certified as a medical device. Code logic produces nutritional deficiency risk estimates for dietary awareness only.
