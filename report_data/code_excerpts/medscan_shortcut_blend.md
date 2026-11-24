# Code Excerpt: `medscan_shortcut_blend`

- **Repository Path**: [`backend/app/services/medscan_service.py`](file:///C:\Users\USER\Desktop\MedNourish-Dev/backend/app/services/medscan_service.py#L11-L38)
- **Lines**: 11–38 (28 lines)
- **Component**: MEDNOURISH Core Implementation

### Architectural Purpose & Design Rationale
Applies confidence discounting (heuristic penalty coefficient 0.55) to classes exhibiting high background shortcut risk, preventing the vision model from exploiting spurious image artifacts.

```python
-> Nutrient crosswalk -> Region follow-up checklist -> Blended inference.
- Blend formula:
  nutrient % = image_evidence * w_img + reference_match * (1 - w_img)
  where w_img = 0.5 normally, 0.25 if shortcut flag detected.
  Image-only results capped at 60.0% and labelled 'image only, low reliability'.
- Kind: 'medscan_blend' (image part labelled 'Image model %').
- Graceful fallback: If ml-service is down, evaluates symptoms only.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import httpx

from app.services.knowledge_service import knowledge_repo, normalize_tag
from app.services.scoring_service import (
    KIND_REFERENCE_MATCH,
    RISK_BAND_LABEL,
    calculate_risk_band,
    scoring_service,
)

logger = logging.getLogger(__name__)

ML_SERVICE_URL = "http://127.0.0.1:8001"
```

> **Educational Prototype Notice**: MEDNOURISH is an academic research prototype and is not certified as a medical device. Code logic produces nutritional deficiency risk estimates for dietary awareness only.
