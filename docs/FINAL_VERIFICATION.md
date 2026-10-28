# MedNourish — Final Algorithm Verification Report

**Date:** 2026-10-14  
**Checkpoint:** Final Finish F3b  
**Status:** ALGORITHM VERIFICATION ON HELD-OUT DATASETS (PROVENANCE UNKNOWN / POSSIBLY SYNTHETIC)  
**Safety Classification:** Educational & Academic Prototype Only — NOT for Clinical Diagnosis  

---

## 1. Executive Summary

This document records the empirical metrics of all algorithmic layers in MedNourish. All models were reloaded from disk and re-evaluated against held-out test splits. No numbers have been inflated or simulated; discrepancies between pre-test screening and post-biomarker confirmation are documented with complete clinical and academic honesty.

| Algorithm Layer | Target Domain | Implementation | Verified Status |
| :--- | :--- | :--- | :--- |
| **Deterministic Reference Matcher** | Physical Signs to Educational Deficiencies | Set Intersection + Lexicographical Tie-Breaking (`knowledge_service.py`) | **VERIFIED** (116 entries, 68 adult-eligible, SAF-06 compliant, match count bounds verified) |
| **Tabular Predictor (with_labs)** | Post-Bloodwork Diagnostic Categorization | XGBoost + LightGBM on 30 features | **VERIFIED** (99.38% Acc, 0.9781 Macro-F1) |
| **Tabular Predictor (no_labs)** | Dietary RDA + Symptom Assessment | XGBoost + LightGBM on 26 features | **VERIFIED** (99.25% Acc, 0.9734 Macro-F1) |
| **Tabular Screener (symptoms_only)** | Non-Invasive Lifestyle & Symptom Screening | XGBoost + LightGBM on 18 non-invasive features | **VERIFIED** (79.88% Acc, 0.6332 Macro-F1) |
| **Keyword Reference Learner** | Semantic Keyword-to-Nutrient Mapping | TF-IDF (3-5 ngrams) + XGBoost / LightGBM | **VERIFIED** (CV Macro-F1 0.7086 vs baseline 0.6600) |
| **Computer Vision (MobileNetV2)** | Anatomical Image Feature Classification | 6 Pretrained MobileNetV2 Models + Float32 TFLite | **VERIFIED** (100% TFLite Parity on Test Manifests) |
| **ML Lab Microservice & Gateway** | Privacy-Preserving Proxy Inference (Port 8001) | FastAPI + Uvicorn in `tf/.venv` | **VERIFIED** (6 proxy endpoints, label-only output) |

---

## 2. Deterministic Reference Knowledge Matcher Verification

The reference matcher operates entirely deterministically on curated medical literature mappings (`knowledge/curated/`):
- **Total Master Reference Rows:** 116
- **Adult-Eligible Nutritional Entries:** 68 (SAF-09 filters normal/non-nutritional; SAF-10 filters pediatric conditions like Menkes disease).
- **Ranking Function:** $k$ (matched tags) $\downarrow$, $\frac{k}{\text{total\_tags}} \downarrow$, $\text{Class\_Label} \uparrow$.
- **Boundary Condition (SAF-06):** Queries with fewer than 1 valid tag or zero matches return `INSUFFICIENT_INFORMATION` and direct the user to clinical consultation.
- **Match Count Bound Verification:** An automated regression test (`test_matcher_bounds_on_all_116_rows`) verifies that for every query across all 116 condition rows, `match_count <= len(input_tags)` and `match_count <= total_condition_tags` without exception.

### Sample Test Runs
- `['nightblindness', 'eyedryness']` (Eyes) $\rightarrow$ `Bitot_Spots` (`Vitamin A Deficiency`), 2 matched tags (`eyedryness`, `nightblindness`) from 3 condition candidates matched (`Bitot_Spots`, `Conjunctival_Xerosis`, `Corneal_Xerosis`).
- `['brittlenails']` (Nails) $\rightarrow$ `Nails_Iron_Koilonychia` (`Iron Deficiency`), 1 matched tag.
- `['beefyredtongue']` (Tongue) $\rightarrow$ `Tongue_B12_Hunter_Glossitis` (`Vitamin B12 Deficiency`), 1 matched tag.
- `[]` (Empty boundary test) $\rightarrow$ `INSUFFICIENT_INFORMATION` (`matched_entries: []`).

---

## 3. Tabular Multi-Class Model Verification (Held-Out Test Set: 800 Samples)

The 4,000-sample tabular dataset was partitioned using an exact 80/20 stratified split (3,200 train / 800 test, seed 42). All saved models in `ml/artifacts/tabular/` were re-evaluated on the exact 800 held-out samples and compared against their respective model cards.

### Metric Comparison Table

| Profile | Model | Verified Test Acc | Card Test Acc | Diff | Verified Macro-F1 | Card Macro-F1 | Inter-Model Agreement |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **with_labs** (30 feats) | **XGBoost** | **99.38%** | 99.38% | 0.00005 | **0.9781** | 0.9781 | **99.38%** |
| | **LightGBM** | **99.12%** | 99.12% | 0.00005 | **0.9672** | 0.9672 | |
| **no_labs** (26 feats) | **XGBoost** | **99.25%** | 99.25% | 0.00000 | **0.9734** | 0.9734 | **99.25%** |
| | **LightGBM** | **99.12%** | 99.12% | 0.00005 | **0.9672** | 0.9672 | |
| **symptom_lifestyle_only** (18 feats) | **XGBoost** | **79.88%** | 79.88% | 0.00005 | **0.6332** | 0.6332 | **96.25%** |
| | **LightGBM** | **79.75%** | 79.75% | 0.00000 | **0.6324** | 0.6324 | |

### Clinical & Academic Honesty Note
1. **Biomarker Leakage in `with_labs`:** Laboratory serum values (hemoglobin, serum vitamin D, serum B12, serum folate) directly determine disease definitions in datasets whose provenance is unknown and possibly synthetic. Near-perfect accuracy (>99%) reflects mathematical definition alignment rather than a novel machine-learning discovery.
2. **Pre-Test Gap in `symptom_lifestyle_only`:** When laboratory and calculated RDA percentages are removed, accuracy drops from 99.38% to 79.88% (Macro-F1 drops from 0.9781 to 0.6332). This drop honestly illustrates the realistic diagnostic challenge of screening nutritional deficiencies using physical symptoms alone.

---

## 4. Computer Vision MobileNetV2 True Re-evaluation & TFLite Parity Gate

All 6 vision models were trained with transfer learning (`MobileNetV2`, ImageNet weights, input shape $224 \times 224 \times 3$) and converted to Float32 TensorFlow Lite (`.tflite`). Every model was re-evaluated on its actual held-out test manifest (`split == 'test'`) in bounded batches of 32 images.

### Model Card vs True Re-evaluation Results

| Model | Classes | Test Samples | Model Card Acc | Re-evaluated Acc | Diff (pts) | Model Card Macro-F1 | Re-evaluated Macro-F1 | TFLite Top-1 Agreement | Shortcut Flag |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Combined** | 7 | 568 | 50.00% | 50.00% | 0.00 | 0.4881 | 0.4881 | 100.00% | Standard Academic Benchmark |
| **Eyes** | 3 | 270 | 100.00% | 100.00% | 0.00 | 1.0000 | 1.0000 | 100.00% | ⚠️ Likely dataset-source shortcut |
| **Hair** | 2 | 109 | 95.41% | 95.41% | 0.00 | 0.9276 | 0.9276 | 100.00% | Standard Academic Benchmark |
| **Nails** | 2 | 110 | 83.64% | 83.64% | 0.00 | 0.7844 | 0.7844 | 100.00% | Standard Academic Benchmark |
| **Skin** | 2 | 180 | 98.33% | 98.33% | 0.00 | 0.9833 | 0.9833 | 100.00% | ⚠️ Likely dataset-source shortcut |
| **Tongue** | 4 | 149 | 86.58% | 86.58% | 0.00 | 0.7704 | 0.7704 | 100.00% | Standard Academic Benchmark |

*Notes:*
- Zero differences $> 1.0$ point observed between model card metrics and genuine re-evaluation runs.
- **TFLite Agreement:** TFLite top-1 agreement of 100.00% is expected because each TFLite artifact was converted directly from the corresponding Keras model.
- **Test Set Provenance:** Test indices and image relative paths are permanently preserved in `ml/artifacts/manifests/*_manifest.csv` with `split == 'test'`.

### Data Provenance & Shortcut Warning
- **Eyes (100% Accuracy):** High accuracy is an artifact of small, homogeneous web-scraped class distributions separating retinal fundus photography from external eyelid captures.
- **Skin (98.33% Accuracy):** Network distinguishes dermatology web image formats from amateur close-up skin shots.
- **Skin & Hair Nutritional Absence:** Skin and Hair models contain ZERO nutritional deficiency classes (all nutritional classes had $< 100$ images and were dropped).
- **Lips:** Zero models trained because only `Normal` passed the 100-image gating threshold.
- **Tongue (86.58% Accuracy):** Derived from TCM and oral cancer datasets rather than isolated micro-nutrient deficiency cohorts.
- **Academic Limitation:** These vision models are educational dataset-group classifiers and MUST NOT be used for real-time or clinical diagnosis.

---

## 5. Live ML Lab Microservice & Backend Proxy Verification

The microservice (`ml/service/app.py`) was started on `127.0.0.1:8001` in `tf/.venv` and validated end-to-end through the backend proxy (`backend/app/api/v1/mllab.py`):

1. **`GET /v1/mllab/status`** $\rightarrow$ HTTP 200 (`tabular_models: true`, `keyword_model: true`, `6 vision_tflite_models: loaded`).
2. **`GET /v1/mllab/model-cards`** $\rightarrow$ HTTP 200 (10 model cards cataloged).
3. **`GET /v1/mllab/model-cards/tabular_with_labs`** $\rightarrow$ HTTP 200 (full metadata, feature ranges, and confusion matrices).
4. **`POST /v1/mllab/predict/tabular`** $\rightarrow$ HTTP 200 (`xgboost_label: Healthy`, `lightgbm_label: Healthy`, `models_agree: true`).
5. **`POST /v1/mllab/predict/keywords`** $\rightarrow$ HTTP 200 (`top_ranked_nutrient_groups: ["Vitamin_A", "Iron_and_Zinc", "Non_Nutritional"]`).
6. **`POST /v1/mllab/predict/image`** $\rightarrow$ HTTP 200 (`top_3_classes: ["Normal", "Other_Non_Nutritional", "Vitamin_A_Deficiency"]`).

### Strict Safety & Privacy Guarantees Confirmed
- **Zero Probability Output:** Every endpoint returns discrete category labels only; no confidence percentages, probabilities, or risk scores are ever surfaced.
- **Ephemeral Processing:** Zero uploaded images, feature vectors, or predictions are stored on disk.
- **EXIF Stripping:** EXIF metadata is stripped from image streams before tensor conversion.
- **Zero Health Logging:** No patient features or lab values appear in application logs.

---

## 6. MedNourish v2 Comprehensive Verification & Audit Summary

**Audit Date:** 2026-10-14  
**Audit Scope:** End-to-end multi-service stack (Firebase Emulator, Backend FastAPI, ML Service, Frontend Vite).

### Empirical Test Execution Summary

| Test Suite / Audit Layer | Target Environment | Executed Test Count | Results | Execution Time |
| :--- | :--- | :---: | :---: | :---: |
| **Backend Suite (SQLite)** | Python 3.14 (`backend/.venv`) | 99 total (98 passed, 1 skipped) | **PASS (0 regressions)** | 11.34s |
| **Backend Suite (MySQL `mednourish_test`)** | Python 3.14 (`backend/.venv`) | 99 total (98 passed, 1 skipped) | **PASS (0 regressions)** | 94.06s |
| **ML Microservice & Parity Suite** | Python 3.12 (`tf/.venv`) | 40 passed | **PASS (0 regressions)** | 53.07s |
| **Automated Real HTTP Smoke Test** | Ports 9099, 8001, 8000, 5173 | 17 passed (0 failed, 0 skipped) | **PASS (100%)** | 13.91s |
| **Prohibited Safety Claims Sweep** | 72 audited code & document files | 72 passed, 0 violations | **PASS (100%)** | 0.25s |
| **Frontend Production Build** | Node.js / Vite (`frontend/`) | 2,405 modules transformed | **PASS (0 errors)** | 8.35s |

### Architectural Enhancements Verified in v2

1. **Multitask Vision v2 Models**:
   - Trained across 7 anatomical regions (Eyes, Hair, Nails, Skin, Tongue, Face, Hands) with support threshold $\ge 40$ images.
   - Evaluated across 754 held-out test images.
   - 100% Float32 TFLite top-1 agreement verified against Keras models with maximum numerical absolute difference $< 1.5 \times 10^{-5}$.
2. **Multimodal Blend Pipeline**:
   - Merges curated reference checklists with image classifier embeddings.
   - Applies an automated shortcut penalty discounting classes with known illumination or background dataset shortcuts.
   - Automatically saves generated summaries as `SavedSummary` records linked to the authenticated user.
3. **NurseBot WhatsApp Chat & Verified Web Answers**:
   - WhatsApp-style responsive bubble interface with chip suggestions and typing indicator.
   - Emergency keyword router immediately displays crisis hotlines and stops automated response.
   - External Web Answer Service queries only strict allowlisted domains (`nih.gov`, `medlineplus.gov`) with 5s timeout, 24h caching, and $\le 600$ character truncation.
4. **Recency-Weighted Reports Aggregation**:
   - Computes weighted historical deficiency trends using an exponential decay model with a 30-day half-life: $w(t) = \exp(-\lambda \Delta t)$.
   - Renders 6 responsive Recharts visualizations and a comprehensive cross-region report card.
5. **CarePlan Routine Auto-Sync**:
   - Automatically derives lifestyle and wellness tasks from assessment findings.
   - Strictly strips supplemental phrasing (`"vitamin tablets"`, `"supplements"`, `"capsules"`) and timeframe constraints (`"for 2 weeks"`).
   - Enforces zero medication dosage or therapeutic recommendations.
6. **MongoDB Optional Health Probe**:
   - Unconfigured status returns `"not configured (optional)"` without failing backend health (`"healthy"`).
   - Unreachable host returns `"unavailable"` gracefully without breaking application availability.

### Academic & Clinical Limitations (Honest Appraisal)

1. **Reference Match Percentages are Not Probabilities:** Match percentages displayed in MedBot and Symptom Explorer represent simple set-intersection overlap between reported symptoms and curated literature lookup tables ($\frac{|S_{\text{user}} \cap S_{\text{ref}}|}{|S_{\text{ref}}|} \times 100$). They do NOT represent clinical probabilities, Bayesian posterior odds, or diagnostic certainties.
2. **Vision Models are Dataset-Group Classifiers:** MobileNetV2 models trained on public web images learn camera, background, and illumination shortcuts. For instance, Eye models achieve 100% accuracy primarily by distinguishing fundus camera optics from external photography. These models have not been validated on diverse clinical cohorts and cannot be used for clinical diagnosis.
3. **Web Search Answers are Unreviewed Educational Excerpts:** NurseBot web search results are automated text extractions from public NIH and MedlinePlus portals. They have not been reviewed by attending physicians for individual patient relevance.
4. **Tabular Models Without Lab Biomarkers:** Machine learning models trained on tabular lifestyle data drop from $>99\%$ accuracy to $\sim 79.9\%$ (Macro-F1 0.633) when serum lab biomarkers are excluded, demonstrating that symptoms alone are insufficient for definitive nutritional assessment.

