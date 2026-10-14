> [!NOTE]
> **HISTORICAL AUDIT SNAPSHOT — SUPERSEDED**
> This document reflects a dated preliminary audit snapshot. For the canonical, byte-verified physical inventory and file reconciliation, refer exclusively to [docs/DATASET_INVENTORY_v2.md](file:///C:/Users/USER/Desktop/MedNourish-Dev/docs/DATASET_INVENTORY_v2.md).

# MEDNOURISH — Computer Vision Pipeline Specification (Phase 3.2 Roadmap)

**Document Date:** 2026-10-13  
**Target Milestone:** Phase 3.2 — Computer Vision Image Classification & TFLite Optimization  
**Architecture Status:** Technical Specification & Quality Gate Definition (Pre-Training)

---

## 1. Overview and Image Corpus Inventory

The MedNourish image collection resides in `datasets/` (372,536 image files across 7 root categories).
Phase 3.2 targets nutritional deficiency signs visible across external physical features (Eyes, Lips, Tongue, Nails, Skin, Hair).

### 1.1 Curated Image Subsets for Educational Vision Prototypes
| Target Anatomical Region | Key Nutritional Indicator Classes | Primary Source Datasets | Notes & Quality Constraints |
|---|---|---|---|
| **Eyes** | `Bitot_Spots`, `Conjunctival_Xerosis`, `Corneal_Xerosis`, `Normal` | `datasets/EYES/Vitamin_A_Deficiency/` & `datasets/EYES/Normal/` | Eliminate fundus/retinopathy images; retain only external ocular surface photos. |
| **Lips / Oral** | `Cheilosis_Angular`, `Normal` | `datasets/LIPS/` | Ensure non-nutritional oral pathologies (e.g. herpes, oral cancer) are excluded. |
| **Tongue** | `Atrophic_Glossitis`, `Magenta_Tongue`, `Normal` | `datasets/TONGUE/` | Exclude uncalibrated traditional diagnostic subcategories unless clinically vetted. |
| **Nails** | `Koilonychia_Spoon_Nails`, `Normal` | `datasets/NAILS/` | Focus on iron-deficiency micro-morphology signs. |

---

## 2. OpenCV Preprocessing & Image Quality Ingestion

### 2.1 Color Space and Resolution Normalization
1. **Color Space Standardization**:
   - OpenCV loads images by default in BGR. All loaders must explicitly convert to RGB:
     `image = cv2.cvtColor(raw_bgr, cv2.COLOR_BGR2RGB)`
2. **Standard MobileNetV2 Input Geometry**:
   - Fixed spatial resolution: **224 × 224 × 3**.
   - Resizing method: Aspect-ratio preserving padding (letterboxing) to prevent non-isotropic morphological distortion of anatomical features:
     ```python
     def resize_with_pad(image, target_size=(224, 224)):
         h, w = image.shape[:2]
         scale = min(target_size[0] / h, target_size[1] / w)
         nh, nw = int(h * scale), int(w * scale)
         resized = cv2.resize(image, (nw, nh), interpolation=cv2.INTER_AREA)
         padded = np.zeros((*target_size, 3), dtype=np.uint8)
         top = (target_size[0] - nh) // 2
         left = (target_size[1] - nw) // 2
         padded[top:top+nh, left:left+nw] = resized
         return padded
     ```
3. **Floating Point Rescaling**:
   - Rescale input pixel range to `[-1.0, 1.0]` as required by standard MobileNetV2 preprocessor (`tf.keras.applications.mobilenet_v2.preprocess_input`).

### 2.2 Quality Assurance Filters (Pre-Training Rejections)
Images failing any of the following automated quality checks will be flagged and excluded:
- **Corrupt File Check**: Images failing `cv2.imread` or truncated JPEG headers.
- **Extreme Blur Detection**: Laplacian variance threshold `cv2.Laplacian(gray, cv2.CV_64F).var() < 100.0`.
- **Severe Underexposure / Overexposure**: Mean luminance `< 30` or `> 225`.
- **Dimension Outliers**: Images with initial resolution smaller than `64 × 64` pixels.

---

## 3. Data Splitting and Leakage Prevention

### 3.1 Patient / Session Grouping
- Many clinical and Kaggle datasets contain multiple photos from the same patient session, burst shots, or augmented copies under sequential filenames (e.g., `IMG_001_1.jpg`, `IMG_001_2.jpg`).
- **Strict Grouping Rule**: Group-aware stratified splitting (`GroupKFold` or `GroupShuffleSplit`) based on patient ID, source directory, or image hash clusters to ensure zero images from the same subject appear across both training and held-out test splits.
- Split ratios: **70% Train / 15% Validation / 15% Test**.

---

## 4. MobileNetV2 Transfer Learning Architecture

### 4.1 Backbone & Classification Head
- **Backbone**: Pre-trained MobileNetV2 (ImageNet weights, top layer excluded).
- **Global Pooling**: Global Average Pooling 2D (`GlobalAveragePooling2D`).
- **Regularization**: Dropout layer with rate `0.3` to prevent overfitting on small clinical cohorts.
- **Output Head**: Dense layer with `softmax` activation corresponding to the number of classes.
- **Loss Function**: `CategoricalCrossentropy(label_smoothing=0.1)` to handle subtle diagnostic boundary ambiguity.

### 4.2 Two-Stage Optimization Schedule
1. **Stage 1 (Feature Extraction)**:
   - Freeze all MobileNetV2 backbone weights (`base_model.trainable = False`).
   - Train only the classification head for 10 epochs using Adam (`lr = 1e-3`).
2. **Stage 2 (Fine-Tuning)**:
   - Unfreeze top 30 layers of MobileNetV2 backbone (`base_model.trainable = True`).
   - Train with a reduced learning rate (`lr = 1e-5`) using early stopping based on validation macro F1.

---

## 5. TensorFlow Lite (TFLite) Conversion & Parity Verification

### 5.1 Optimization Targets
To run in browser or lightweight client runtimes (WebAssembly or on-device mobile):
1. **Default Float32 TFLite**:
   - Direct conversion: `tf.lite.TFLiteConverter.from_keras_model(model)`.
2. **Post-Training Dynamic Range Quantization**:
   - Reduces weight footprint from ~14 MB to ~3.5 MB:
     `converter.optimizations = [tf.lite.Optimize.DEFAULT]`.

### 5.2 Original vs. TFLite Parity Verification Gate
Before any TFLite model artifact is approved:
- Evaluate both models on the identical 600-sample test set.
- **Maximum Absolute Discrepancy Gate**: `max(|P_keras(y|x) - P_tflite(y|x)|) < 0.01` for float32.
- **Top-1 Categorical Agreement**: Must achieve `>= 99.5%` identical top-1 class predictions between Keras and TFLite.

---

## 6. Integration Boundaries & Application Safety

1. **Standalone Experimental Prototype**:
   - Computer vision pipelines execute inside `ml/` and output unlinked diagnostic experimental models.
2. **Zero Direct Health Advice Linkage**:
   - Under `SAF-01`, `SAF-04`, `SAF-07`, and `GR-05`, no image classifier output shall be presented to users as a medical diagnosis, definitive deficiency claim, or certainty score.
   - Any future UI integration must strictly present results as `"Educational Reference Sign Matches"` with mandatory disclaimer banners and prompts to seek clinical consultation.
