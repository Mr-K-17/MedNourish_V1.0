# Code Excerpt: `tabular_preprocessor`

- **Repository Path**: [`ml/train_tabular.py`](file:///C:\Users\USER\Desktop\MedNourish-Dev/ml/train_tabular.py#L1-L30)
- **Lines**: 1–30 (30 lines)
- **Component**: MEDNOURISH Core Implementation

### Architectural Purpose & Design Rationale
Prepares 4,000 tabular clinical records across three feature profiles (with_labs, no_labs, symptoms_only). Purges biochemical target leakage features (Ferritin, Vitamin D) to ensure honest real-world evaluation.

```python
"""
MedNourish — Complete Stage 2 Tabular ML Pipeline
=================================================
Executes:
(a) Main CSV (4,000x34) tabular training & evaluation across three profiles:
    - with_labs (full clinical laboratory serum features, near-perfect accuracy >99%)
    - no_labs (dietary RDA + symptoms + lifestyle/demographics, ~99%)
    - symptom_lifestyle_only (strictly non-invasive symptoms + demographics, ~79% accuracy, showing realistic clinical pre-test gap)
    Evaluated with 5-fold CV on train split and held-out test evaluation.
(b) 116-row Master Reference Table keyword-to-nutrient learner using character n-gram TF-IDF (3-5)
    + Body_Region one-hot, evaluated with Stratified 5-Fold CV comparing XGBoost, LightGBM, and Deterministic Baseline.
    Strictly marked: reference-table learner, NOT a patient predictor.
(c) Model exports and comprehensive JSON model cards to ml/artifacts/tabular/.
"""

import json
import os
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any
from collections import Counter
import numpy as np

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, classification_report, confusion_matrix
```

> **Educational Prototype Notice**: MEDNOURISH is an academic research prototype and is not certified as a medical device. Code logic produces nutritional deficiency risk estimates for dietary awareness only.
