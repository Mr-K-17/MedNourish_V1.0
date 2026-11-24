# Code Excerpt: `reports_aggregation`

- **Repository Path**: [`backend/app/services/reports_aggregate_service.py`](file:///C:\Users\USER\Desktop\MedNourish-Dev/backend/app/services/reports_aggregate_service.py#L1-L30)
- **Lines**: 1–30 (30 lines)
- **Component**: MEDNOURISH Core Implementation

### Architectural Purpose & Design Rationale
Executes exponential time-decay weighting (half-life = 7.0 days, lambda = 0.099) across historical Explorer, MedBot, and MedScan assessments to synthesize a unified temporal deficiency trajectory.

```python
"""Reports Aggregate & Multi-Engine Analytics Service (Phase 5).

Guarantees:
- Aggregates up to 5 most recent SavedSummary snapshots with recency weights:
  Base weights = [0.35, 0.25, 0.20, 0.12, 0.08] normalized to sum 1.0.
- Blends Reference %, XGBoost %, LightGBM %, and Image %.
- Generates payloads for all 6 Recharts visual components:
  1. Grouped Bar (nutrient x engine source)
  2. Ranked Horizontal Bar (final % and risk band)
  3. Radar (multi-axial nutrient pattern)
  4. Donut (risk band counts)
  5. Timeline (longitudinal tracking over check-in dates)
  6. Heatmap (body-region x nutrient matrix)
- Generates Final Report Card with probable deficiencies, demo risk band, supporting sources, and suggested measures.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.user import SavedSummary
from app.schemas.reports import (
    AggregatedNutrientItem,
    ChartDataPayload,
    FinalReportCard,
    ReportsAggregateResponse,
)

logger = logging.getLogger(__name__)
```

> **Educational Prototype Notice**: MEDNOURISH is an academic research prototype and is not certified as a medical device. Code logic produces nutritional deficiency risk estimates for dietary awareness only.
