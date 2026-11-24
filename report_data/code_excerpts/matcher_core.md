# Code Excerpt: `matcher_core`

- **Repository Path**: [`backend/app/services/scoring_service.py`](file:///C:\Users\USER\Desktop\MedNourish-Dev/backend/app/services/scoring_service.py#L1-L32)
- **Lines**: 1–32 (32 lines)
- **Component**: MEDNOURISH Core Implementation

### Architectural Purpose & Design Rationale
Core inverted-index symptom matcher resolving candidate conditions against user-selected clinical signs. Computes candidate match overlap and extracts condition-specific weight vectors deterministically.

```python
"""Scoring Service for Deterministic Reference Match Calculations.

Implements Phase 2 / docs/SCORING_SPEC.md:
- Inverse Document Frequency (IDF) weighting for condition row keywords.
- Small-evidence shrinkage so single tags cannot yield 100% (capped at 95.0%).
- Noisy-OR aggregation across adult-eligible condition rows for each nutrient group.
- Demo risk bands: High (>= 60), Moderate (30-59), Low (< 30).
- Retains old tag-count fields for transparency ("why" details).
- Strictly preserves SAF-09 (nutritional only) and SAF-10 (pediatric exclusions).
- Fully deterministic and monotonic.
"""

import math
from typing import Any, Dict, List, Optional, Set
from app.services.knowledge_service import (
    KnowledgeRepository,
    ReferenceEntry,
    knowledge_repo,
    normalize_tag,
    PACKAGE_VERSION,
    MATCHER_VERSION,
)

KIND_REFERENCE_MATCH = "Reference match %"
RISK_BAND_LABEL = "Demo risk band (heuristic, not clinical)"
EXPLANATION_REFERENCE_MATCH = (
    "Deterministic coverage of reference database symptom patterns, not a clinical diagnosis or test."
)

# Thresholds per docs/SCORING_SPEC.md & owner amendments
THRESHOLD_HIGH = 60.0
THRESHOLD_MODERATE = 30.0
```

> **Educational Prototype Notice**: MEDNOURISH is an academic research prototype and is not certified as a medical device. Code logic produces nutritional deficiency risk estimates for dietary awareness only.
