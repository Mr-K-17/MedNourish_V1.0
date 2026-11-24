# Code Excerpt: `vision_model_builder`

- **Repository Path**: [`ml/train_vision_v2.py`](file:///C:\Users\USER\Desktop\MedNourish-Dev/ml/train_vision_v2.py#L1-L32)
- **Lines**: 1–32 (32 lines)
- **Component**: MEDNOURISH Core Implementation

### Architectural Purpose & Design Rationale
Constructs the MobileNetV2 transfer learning architecture (160x160x3 input) with inverted residuals, GlobalAveragePooling2D, dropout (0.2), and dense softmax classification for 7 regional anatomical targets.

```python
"""
MedNourish — Phase 3 v2 MobileNetV2 Training, Parity & Evaluation
==================================================================
Spec: Phase 3 (a)
- Trains 7 MobileNetV2 models for:
  eyes, hair, lips, nails, skin, tongue, combined (10 retained vitamin classes)
- Data augmentation on TRAIN only (flip, small rotation, brightness)
- Class weighting
- Bounded epochs & early stopping
- Held-out test evaluation
- Small-sample flag + bootstrap 95% CI for accuracy for classes under 100 images
- TFLite Float32 parity verification with real tf.lite.Interpreter (max diff < 0.01, top-1 >= 99.5%)
- Shortcut-check badges (24-bin color histogram + size)
- Writes all artifacts to ml/artifacts/v2/vision/
"""

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
import tensorflow as tf

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
```

> **Educational Prototype Notice**: MEDNOURISH is an academic research prototype and is not certified as a medical device. Code logic produces nutritional deficiency risk estimates for dietary awareness only.
