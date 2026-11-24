# Code Excerpt: `careplan_meal_planner`

- **Repository Path**: [`backend/app/services/meal_plan_service.py`](file:///C:\Users\USER\Desktop\MedNourish-Dev/backend/app/services/meal_plan_service.py#L1-L32)
- **Lines**: 1–32 (32 lines)
- **Component**: MEDNOURISH Core Implementation

### Architectural Purpose & Design Rationale
Synthesizes daily meal and micronutrient recommendations from curated food_items.csv based on detected deficiency risks and user dietary constraints (e.g. Vegan, Caloric budget) with 0 string truncation.

```python
"""Meal Plan Service for Deterministic 7-Day CarePlan Meal Planning (Phase 5 / C-39).

Guarantees:
- Deterministic: same inputs -> exact same plan.
- Foods only: strictly zero medications, supplements, doses, calories, or grams (C-08, C-22, C-39).
- Respects diet preferences: vegan, veg, eggetarian, nonveg.
- Respects allergens: celiac (no gluten), lactose intolerance (no dairy), nuts, eggs, fish, soy.
- Respects cautions: diabetes (no high_sugar), hypertension (no high_sodium), kidney (no high_potassium).
- Adds doctor consultation line for kidney disease, liver disease, or type 1 diabetes.
- Focus nutrients covered by >= 2 meals/day, fiber every day.
- No consecutive-day repeat of main dishes.
- First report entry creates the first active plan immediately.
- Replaces active plan only if focus nutrient set changes or top percentage moves >= 10 points.
"""

import csv
from datetime import datetime, date, timedelta
import hashlib
import json
import logging
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy.orm import Session
from app.models.user import (
    CarePlanMealLog,
    CarePlanMealPlan,
    CarePlanPrefs,
    UserProfile,
    SavedSummary,
```

> **Educational Prototype Notice**: MEDNOURISH is an academic research prototype and is not certified as a medical device. Code logic produces nutritional deficiency risk estimates for dietary awareness only.
