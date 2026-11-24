# Code Excerpt: `tflite_parity_check`

- **Repository Path**: [`ml/reevaluate_vision.py`](file:///C:\Users\USER\Desktop\MedNourish-Dev/ml/reevaluate_vision.py#L1-L30)
- **Lines**: 1–30 (30 lines)
- **Component**: MEDNOURISH Core Implementation

### Architectural Purpose & Design Rationale
Evaluates numerical agreement and top-1 prediction parity between Float32 Keras checkpoints and Dynamic Range Quantized (DRQ) INT8 TFLite models on unseen test splits.

```python
"""
MedNourish — True Vision Model Re-evaluation on Held-Out Test Manifests
======================================================================
Loads each of the 6 vision models (.keras and .tflite),
reads the test manifest rows (split == 'test'),
evaluates predictions in bounded batches of 32,
and outputs exact re-evaluation metrics alongside model card metrics.
"""

import csv
import json
import os
import sys
import time
from pathlib import Path
import numpy as np
import tensorflow as tf
from sklearn.metrics import accuracy_score, f1_score

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ml.image_pipeline import load_image_rgb, resize_with_pad

MANIFESTS_DIR = Path("ml/artifacts/manifests")
VISION_ARTIFACTS_DIR = Path("ml/artifacts/vision")

MODELS = ["combined", "eyes", "hair", "nails", "skin", "tongue"]

def reevaluate_all():
```

> **Educational Prototype Notice**: MEDNOURISH is an academic research prototype and is not certified as a medical device. Code logic produces nutritional deficiency risk estimates for dietary awareness only.
