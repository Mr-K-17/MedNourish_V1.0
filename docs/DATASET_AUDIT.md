> [!NOTE]
> **HISTORICAL AUDIT SNAPSHOT — SUPERSEDED**
> This document reflects a dated preliminary audit snapshot. For the canonical, byte-verified physical inventory and file reconciliation, refer exclusively to [docs/DATASET_INVENTORY_v2.md](DATASET_INVENTORY_v2.md).

# MEDNOURISH — Dataset Audit Report

**Date of Audit:** 2026-10-12  
**Audit Scope:** Complete read-only audit of all datasets, structured CSV files, annotation files, notebooks, and image collections in the MEDNOURISH workspace (`c:\Users\USER\Desktop\MedNourish\datasets\`).  
**Status:** Audit Complete — Phase 0 Read-Only Inspection  
**Governing Principle:** Evidence first, documentation second, implementation only after explicit approval. All original dataset files remain strictly read-only and unmodified.

---

## 1. Executive Summary

A comprehensive, automated, and reproducible inspection was executed across the entire `datasets/` repository.

### Key Empirical Findings:
1. **Total Image Files:** 372,536 image files across 7 primary body-region/collection directories.
2. **Total Structured CSV Files:** 34 CSV files found in the repository (not only the 13 in `MedBot_datasets/`).
   - The 13 `MedBot_datasets/` reference CSVs exist and are verified.
   - 12 identical duplicate copies exist across the body-region folders (`EYES/`, `HAIR/`, `LIPS/`, `NAILS/`, `SKIN/`, `TONGUE/`).
   - 8 specialized tabular/label files exist for ocular conditions, glaucoma, hypertensive retinopathy, hair, and dermatological datasets.
   - 1 main structured dataset exists at `datasets/vitamin_deficiency_disease_dataset_20260123.csv` (4,000 data rows × 34 columns).
3. **Total Annotation Files:** 21,902 files (`.xml`, `.txt`, `.json`, `.mat`, `.yaml`).
4. **Notebooks:** 4 Jupyter notebooks (`.ipynb`) exist with exploratory data analysis or external Kaggle provenance metadata.
5. **Data Structure Marker:** `datasets/DATASET_STRUCTURE.txt` is present and **0 bytes** (empty).
6. **Provenance & Licensing:** The vast majority of datasets carry Kaggle or external research provenance markers (e.g. Kaggle datasetVersion IDs, "VitaCore MedScan", ORIGA academic-only glaucoma dataset). No commercial or public redistribution licences are verified.

---

## 2. Inventory of Structured Datasets (CSVs)

### 2.1 The 13 `MedBot_datasets/` Files

Located in `datasets/MedBot_datasets/`:

| File Name | Size (Bytes) | Rows | Cols | Mismatched Rows | Exact Dupes | Observed Content / Category |
|---|---|---|---|---|---|---|
| `Eyes_Symptoms_vs_Vitamin_Deficiency_Mapping.csv` | 5,782 | 15 | 9 | 0 | 0 | Reference mapping: 15 ocular condition classes |
| `Eyes_Vitamin_Deficiency_to_Suggested_Routine.csv` | 6,848 | 10 | 7 | 0 | 0 | Routine recommendations: 10 deficiency entries |
| `Hair_Symptoms_vs_Vitamin_Deficiency_Mapping.csv` | 13,046 | 32 | 10 | 1 | 0 | Reference mapping: 32 hair condition classes (Line 31 malformed) |
| `Hair_Vitamin_Deficiency_to_Suggested_Routine.csv` | 14,784 | 25 | 7 | 1 | 0 | Routine recommendations: 25 deficiency entries (Line 24 malformed) |
| `Lips_Symptoms_vs_Vitamin_Deficiency_Mapping.csv` | 6,050 | 14 | 9 | 0 | 0 | Reference mapping: 14 lip condition classes |
| `Lips_Vitamin_Deficiency_to_Suggested_Routine.csv` | 9,141 | 14 | 7 | 0 | 0 | Routine recommendations: 14 deficiency entries |
| `MedNourish_Symptom_Keywords_vs_Vitamin_Deficiency_Mapping.csv` | 13,114 | 116 | 5 | 0 | 0 | Master keyword lookup: 116 rows across 6 body regions |
| `Nails_Symptoms_vs_Vitamin_Deficiency_Mapping.csv` | 6,817 | 16 | 9 | 0 | 0 | Reference mapping: 16 nail condition classes |
| `Nails_Vitamin_Deficiency_to_Suggested_Routine.csv` | 7,772 | 12 | 7 | 0 | 0 | Routine recommendations: 12 deficiency entries |
| `Skin_Symptoms_vs_Vitamin_Deficiency_Mapping.csv` | 9,808 | 23 | 9 | 0 | 0 | Reference mapping: 23 skin condition classes |
| `Skin_Vitamin_Deficiency_to_Suggested_Routine.csv` | 5,193 | 7 | 7 | 0 | 0 | Routine recommendations: 7 deficiency entries |
| `Tongue_Symptoms_vs_Vitamin_Deficiency_Mapping.csv` | 6,974 | 16 | 9 | 0 | 0 | Reference mapping: 16 tongue condition classes |
| `Tongue_Vitamin_Deficiency_to_Suggested_Routine.csv` | 9,515 | 15 | 7 | 0 | 0 | Routine recommendations: 15 deficiency entries |

**Total Classes Mapped:** 15 (Eyes) + 32 (Hair) + 14 (Lips) + 16 (Nails) + 23 (Skin) + 16 (Tongue) = **116 condition classes**, matching exactly the 116 rows in the Master Keyword Mapping file.  
**Total Routine Rows:** 10 + 25 + 14 + 12 + 7 + 15 = **83 routine entries**.

#### Malformed Row Inspection Evidence:
1. **`Hair_Symptoms_vs_Vitamin_Deficiency_Mapping.csv` (Line 31):**
   - Header has 10 columns: `Class_Label, Category, Subcategory, Vitamin_Deficiency, Associated_Nutrient, Key_Symptoms, Visible_Hair_Signs, Common_Systemic_Symptoms, Risk_Factors, Severity_Level`.
   - Line 31 contains unquoted commas in fields: `'Structural (Genetic, Rarely Metabolic)'` and `'Rarely Copper-Related (e.g., Menkes disease in infants)'`, causing CSV parsers to split the single row into 12 columns instead of 10.
2. **`Hair_Vitamin_Deficiency_to_Suggested_Routine.csv` (Line 24):**
   - Header has 7 columns: `Vitamin_Deficiency, Associated_Nutrient, Dietary_Recommendations, Suggested_Supplementation, Lifestyle_Routine, Follow_Up_Recommendation, Disclaimer`.
   - Line 24 contains unquoted commas in fields: `'Structural (Genetic, Rarely Metabolic)'` and `'Rarely Copper-Related (e.g., Menkes disease in infants)'`, causing CSV parsers to split into 9 columns instead of 7.

### 2.2 Duplication in Body Region Directories
Exact byte-for-byte duplicate SHA-256 hashes confirm that 12 of the 13 reference CSV files are replicated inside the corresponding body region folders (`datasets/EYES/`, `datasets/HAIR/`, etc.). The only file unique to `MedBot_datasets/` is `MedNourish_Symptom_Keywords_vs_Vitamin_Deficiency_Mapping.csv`.

### 2.3 Other Tabular Datasets in the Repository

1. **`datasets/vitamin_deficiency_disease_dataset_20260123.csv`**
   - **Size:** 742,012 bytes.
   - **Rows:** 4,000 data rows (plus 1 header row).
   - **Columns:** 34 columns.
   - **Encoding:** UTF-8.
   - **Missing Values:** 0 missing or blank values across all 34 columns.
   - **Exact Duplicates:** 0 exact duplicate rows.
   - **Target Column (`disease_diagnosis`):**
     - `Healthy`: 1,509 (37.7%)
     - `Anemia`: 1,245 (31.1%)
     - `Rickets_Osteomalacia`: 1,029 (25.7%)
     - `Night_Blindness`: 122 (3.1%)
     - `Scurvy`: 95 (2.4%)
   - **Nature:** Tabular synthetic/observational patient records containing laboratory serum measurements (`hemoglobin_g_dl`, `serum_vitamin_d_ng_ml`, `serum_vitamin_b12_pg_ml`, `serum_folate_ng_ml`) and dietary RDA percentages (`vitamin_a_percent_rda`, etc.). These features are clinical/lab parameters that the MedNourish web questionnaire will **not** collect. Furthermore, the 5 target labels do not match the 116 condition classes in the reference mapping tables.

2. **Ocular & Retinopathy Datasets (`datasets/EYES/Other_Ocular_Conditions/`):**
   - `Glaucoma/G1020.csv`: 1,020 rows × 2 columns (image file mappings).
   - `Glaucoma/glaucoma.csv`: 650 rows × 5 columns (cup-to-disc ratio and optic disc metrics).
   - `Hypertensive_Retinopathy/.../HRDC Hypertensive Classification Training Labels.csv`: 712 rows × 2 cols.
   - `Hypertensive_Retinopathy/.../HRDC Hypertensive Retinopathy Classification Training Labels.csv`: 712 rows × 2 cols.
   - `Ocular Conditions/dataset.csv`: 9 rows × 3 cols (1 malformed row).

3. **Dermatology Datasets (`datasets/SKIN/OTHER/`):**
   - `balanced_dataset.csv` and `balanced_dataset/balanced_dataset.csv`: 245,442 rows × 2 columns (`image_path, label`). 463 duplicate rows detected. Represents a very large external dermatological image classification benchmark.

---

## 3. Inventory of Image Datasets

Audit performed via recursive file system analysis counting confirmed image extensions (`.jpg`, `.jpeg`, `.png`, `.webp`, `.tif`, `.jfif`, `.gif`, `.avif`, `.svg`):

| Region / Top-Level Directory | Image File Count | Subdirectory Structure / Classes | Annotations / Non-Image Metadata |
|---|---|---|---|
| `datasets/EYES/` | 44,925 | `Normal`, `Nutritional_Optic_Conditions`, `Other_Ocular_Conditions`, `Vitamin_A_Deficiency` | 1,678 annotations (`.mat`, `.txt`, `.json`), 1 notebook (`eye-diseases-classification.ipynb`) |
| `datasets/HAIR/` | 2,349 | `Alopecia`, `Corkscrew_Hair`, `Normal`, `Other`, `Sparse_Hair` | 6 annotations (`annotations.xml`, `README.txt`) |
| `datasets/LIPS/` | 10,324 | `NON_NUTRITIONAL`, `NORMAL`, `NUTRITIONAL` | 14 annotations (`README.txt`), 1 notebook (`lip-segmentation-with-attention-unet.ipynb`) |
| `datasets/NAILS/` | 2,278 | `NON_NUTRITIONAL`, `NORMAL`, `NUTRITIONAL`, `OTHER` | 16 annotations (`README.txt`) |
| `datasets/SKIN/` | 266,443 | `BIOTIN`, `NORMAL`, `OTHER`, `PROTEIN_ENERGY_MALNUTRITION`, `VITAMIN_A`, `VITAMIN_B3`, `VITAMIN_C`, `ZINC` | 24 annotations (`README.txt`), 1 notebook (`vitamin-deficiency-skin-signs.ipynb`), 245K row CSV |
| `datasets/TONGUE/` | 20,585 | `Diabetes`, `Healthy`, `OralCancer`, `Pre Diabetes`, `shezhen datasets` | 20,163 annotations (COCO `.json`, YOLO `.txt`, Pascal VOC `.xml`, `shezhenv3-txt.yaml`) |
| `datasets/dataset/` | 25,632 | 11 deficiency folders: `Vitamin A deficiency`, `Vitamin B complex deficiency`, `Vitamin B-12 deficiency`, `Vitamin B2 deficiency`, `Vitamin B3 deficieny`, `Vitamin B9 deficiency`, `Vitamin C deficiency`, `Vitamin D deficiency`, `Vitamin E deficiency`, `Vitamin K deficiency`, `zinc, iron, biotin, or protein deficiency` | 0 annotations |
| **TOTAL** | **372,536** | — | **21,902** |

---

## 4. Quality, Clinical and Safety Findings

### 4.1 Unsupported Medical and Clinical Content in Reference CSVs
1. **Pediatric and Infant Content:**
   - Analysis revealed **22 instances** of pediatric terms (`infant`, `child`, `pediatric`, `baby`, `toddler`) across the reference mapping CSVs.
   - *Example:* Line 31 of Hair mapping references "Menkes disease in infants".
   - *Safety Constraint:* Project Decision `C-01` strictly establishes the product as an academic demo for **adults aged 18 and above**. Pediatric entries must be excluded or flagged during Tier 2 cleaning.
2. **Medicines, Supplements, and Dosages:**
   - Analysis revealed **31 instances** of drug and supplement terminology (`supplement`, `dose`, `iu`, `mg`, `mcg`, `medication`, `prescription`, `injection`, `capsule`, `tablet`).
   - *Example:* Routine tables recommend specific therapeutic doses (e.g. "Vitamin A 200,000 IU", "copper-histidine therapy under specialist care").
   - *Safety Constraint:* Project Decision `C-08` and Rule `SAF-08` forbid displaying medicines, supplements, doses, or treatment courses. These columns must be stripped from user-facing packages.
3. **Non-Nutritional Pathologies:**
   - Datasets contain conditions outside the scope of nutritional deficiencies, such as `OralCancer`, `Diabetes`, `Lichen Planus`, `Glaucoma`, and `Hypertensive Retinopathy`.
   - *Safety Constraint:* Decision `C-18` dictates that non-nutritional classes must not be displayed as nutritional deficiencies or suggested to users in Phase 1.

### 4.2 Tabular ML Data Suitability (Main CSV PV-01 & PV-02)
- The main CSV contains 4,000 rows with 34 columns.
- Features include laboratory blood draw results (`hemoglobin_g_dl`, `serum_vitamin_d_ng_ml`, etc.) and diet RDA numbers that a self-guided user cannot enter in a questionnaire.
- The 5 target classes (`Healthy`, `Anemia`, `Rickets_Osteomalacia`, `Night_Blindness`, `Scurvy`) represent broad clinical syndromes rather than specific isolated nutrient deficiencies matching the 116 mapped classes.
- The ETL notebook (`vitamin-deficiency-disease-prediction-dataset-etl.ipynb`) consists solely of visualization code with Seaborn and Pandas; it contains zero model training, cross-validation, or evaluation logic.
- **Verdict:** Unsuitable for training a user-facing questionnaire predictor. Tabular ML must remain gated and deferred to Phase 2.

### 4.3 Image Datasets Suitability (MedScan Phase 2 PV-04 to PV-06)
- The image collections comprise 372,536 files from multiple heterogeneous sources (Kaggle datasets, ORIGA, Roboflow Shezhen tongue annotations, VitaCore placeholder folders).
- Folder taxonomy does not match between `dataset/` (11 deficiency categories) and the anatomical folders (`EYES`, `SKIN`, `TONGUE`, etc.).
- `EYES/` and `TONGUE/` contain non-nutritional pathologies (Glaucoma, Oral Cancer, Diabetes).
- Provenance and redistribution licences are unverified.
- **Verdict:** MedScan image analysis cannot be included in Phase 1 MVP. It must remain strictly deferred to Phase 2, behind gates G1–G6.

---

## 5. Audit Deliverable Status & Next Actions

1. **Phase 0 Status:** In progress. Dataset audit is complete.
2. **Cleaned Knowledge Package:** A future Tier 1 & Tier 2 cleaning pipeline must be established in `knowledge/` with reproducible scripts, leaving `datasets/` untouched.
3. **Documentation Alignment:** Master registers in `docs/Memory.md` must be synchronized with decisions C-13 through C-24, OD-16 through OD-21, and PV-18/19.
