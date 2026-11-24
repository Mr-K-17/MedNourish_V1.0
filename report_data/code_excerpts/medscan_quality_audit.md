# Code Excerpt: `medscan_quality_audit`

- **Repository Path**: [`backend/app/services/medscan_service.py`](file:///C:\Users\USER\Desktop\MedNourish-Dev/backend/app/services/medscan_service.py#L1-L28)
- **Lines**: 1–28 (28 lines)
- **Component**: MEDNOURISH Core Implementation

### Architectural Purpose & Design Rationale
Enforces input image quality gating using cv2.Laplacian variance for blur detection (threshold >= 50.0) and grayscale mean intensity for illumination bounding (40 <= mean <= 225). Rejects invalid images.

```python
"""
MedNourish — Backend MedScan Blend Service (Phase 3.c)
=====================================================
Module: app.services.medscan_service
Spec: Phase 3 (c)

Architectural Guarantees:
- Backend NEVER imports TensorFlow or OpenCV.
- Communicates with ml-service on http://127.0.0.1:8001 via httpx.
- Quality check -> Model selection -> Image prediction (Image model %)
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
```

> **Educational Prototype Notice**: MEDNOURISH is an academic research prototype and is not certified as a medical device. Code logic produces nutritional deficiency risk estimates for dietary awareness only.
