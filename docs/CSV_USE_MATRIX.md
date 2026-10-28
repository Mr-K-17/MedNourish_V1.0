# MedNourish — Complete 34-CSV Audit & Use Matrix

**Audit Date:** 2026-10-14  
**Dataset Source:** `C:\Users\USER\Desktop\MedNourish\datasets`  
**Total CSV Files Audited:** 34  

This document audits every CSV file found within `datasets/`, specifying its schema, dimensions, duplicates, encoding, operational classification, and justification.

---

## 1. Summary Matrix

| # | CSV Path | Rows | Cols | Dups | Encoding | Operational Category |
|---|---|---|---|---|---|---|
| 1 | `EYES/Eyes_Symptoms_vs_Vitamin_Deficiency_Mapping.csv` | 15 | 9 | 0 | utf-8 | **Used as Reference Lookup (Duplicate)** |
| 2 | `EYES/Eyes_Vitamin_Deficiency_to_Suggested_Routine.csv` | 10 | 7 | 0 | utf-8 | **Used as Reference Lookup (Duplicate)** |
| 3 | `EYES/Other_Ocular_Conditions/Glaucoma/G1020.csv` | 1020 | 2 | 0 | utf-8 | **Excluded** |
| 4 | `EYES/Other_Ocular_Conditions/Glaucoma/glaucoma.csv` | 650 | 5 | 0 | utf-8 | **Excluded** |
| 5 | `EYES/Other_Ocular_Conditions/Hypertensive_Retinopathy/1-Hypertensive Classification/1-Hypertensive Classification/2-Groundtruths/HRDC Hypertensive Classification Training Labels.csv` | 712 | 2 | 0 | utf-8 | **Excluded** |
| 6 | `EYES/Other_Ocular_Conditions/Hypertensive_Retinopathy/2-Hypertensive Retinopathy Classification/2-Hypertensive Retinopathy Classification/2-Groundtruths/HRDC Hypertensive Retinopathy Classification Training Labels.csv` | 712 | 2 | 0 | utf-8 | **Excluded** |
| 7 | `EYES/Other_Ocular_Conditions/Ocular Conditions/dataset.csv` | 9 | 3 | 0 | utf-8 | **Excluded** |
| 8 | `HAIR/Hair_Symptoms_vs_Vitamin_Deficiency_Mapping.csv` | 32 | 10 | 0 | utf-8 | **Used as Reference Lookup (Duplicate)** |
| 9 | `HAIR/Hair_Vitamin_Deficiency_to_Suggested_Routine.csv` | 25 | 7 | 0 | utf-8 | **Used as Reference Lookup (Duplicate)** |
| 10 | `HAIR/Other/dataset_info.csv` | 98 | 4 | 0 | utf-8 | **Excluded** |
| 11 | `LIPS/Lips_Symptoms_vs_Vitamin_Deficiency_Mapping.csv` | 14 | 9 | 0 | utf-8 | **Used as Reference Lookup (Duplicate)** |
| 12 | `LIPS/Lips_Vitamin_Deficiency_to_Suggested_Routine.csv` | 14 | 7 | 0 | utf-8 | **Used as Reference Lookup (Duplicate)** |
| 13 | `MedBot_datasets/Eyes_Symptoms_vs_Vitamin_Deficiency_Mapping.csv` | 15 | 9 | 0 | utf-8 | **Used as Reference Lookup** |
| 14 | `MedBot_datasets/Eyes_Vitamin_Deficiency_to_Suggested_Routine.csv` | 10 | 7 | 0 | utf-8 | **Used as Reference Lookup** |
| 15 | `MedBot_datasets/Hair_Symptoms_vs_Vitamin_Deficiency_Mapping.csv` | 32 | 10 | 0 | utf-8 | **Used as Reference Lookup** |
| 16 | `MedBot_datasets/Hair_Vitamin_Deficiency_to_Suggested_Routine.csv` | 25 | 7 | 0 | utf-8 | **Used as Reference Lookup** |
| 17 | `MedBot_datasets/Lips_Symptoms_vs_Vitamin_Deficiency_Mapping.csv` | 14 | 9 | 0 | utf-8 | **Used as Reference Lookup** |
| 18 | `MedBot_datasets/Lips_Vitamin_Deficiency_to_Suggested_Routine.csv` | 14 | 7 | 0 | utf-8 | **Used as Reference Lookup** |
| 19 | `MedBot_datasets/MedNourish_Symptom_Keywords_vs_Vitamin_Deficiency_Mapping.csv` | 116 | 5 | 0 | utf-8 | **Used for Training & Reference** |
| 20 | `MedBot_datasets/Nails_Symptoms_vs_Vitamin_Deficiency_Mapping.csv` | 16 | 9 | 0 | utf-8 | **Used as Reference Lookup** |
| 21 | `MedBot_datasets/Nails_Vitamin_Deficiency_to_Suggested_Routine.csv` | 12 | 7 | 0 | utf-8 | **Used as Reference Lookup** |
| 22 | `MedBot_datasets/Skin_Symptoms_vs_Vitamin_Deficiency_Mapping.csv` | 23 | 9 | 0 | utf-8 | **Used as Reference Lookup** |
| 23 | `MedBot_datasets/Skin_Vitamin_Deficiency_to_Suggested_Routine.csv` | 7 | 7 | 0 | utf-8 | **Used as Reference Lookup** |
| 24 | `MedBot_datasets/Tongue_Symptoms_vs_Vitamin_Deficiency_Mapping.csv` | 16 | 9 | 0 | utf-8 | **Used as Reference Lookup** |
| 25 | `MedBot_datasets/Tongue_Vitamin_Deficiency_to_Suggested_Routine.csv` | 15 | 7 | 0 | utf-8 | **Used as Reference Lookup** |
| 26 | `NAILS/Nails_Symptoms_vs_Vitamin_Deficiency_Mapping.csv` | 16 | 9 | 0 | utf-8 | **Used as Reference Lookup (Duplicate)** |
| 27 | `NAILS/Nails_Vitamin_Deficiency_to_Suggested_Routine.csv` | 12 | 7 | 0 | utf-8 | **Used as Reference Lookup (Duplicate)** |
| 28 | `SKIN/OTHER/balanced_dataset.csv` | 245442 | 2 | 463 | utf-8 | **Excluded** |
| 29 | `SKIN/OTHER/balanced_dataset/balanced_dataset.csv` | 245442 | 2 | 463 | utf-8 | **Excluded** |
| 30 | `SKIN/Skin_Symptoms_vs_Vitamin_Deficiency_Mapping.csv` | 23 | 9 | 0 | utf-8 | **Used as Reference Lookup (Duplicate)** |
| 31 | `SKIN/Skin_Vitamin_Deficiency_to_Suggested_Routine.csv` | 7 | 7 | 0 | utf-8 | **Used as Reference Lookup (Duplicate)** |
| 32 | `TONGUE/Tongue_Symptoms_vs_Vitamin_Deficiency_Mapping.csv` | 16 | 9 | 0 | utf-8 | **Used as Reference Lookup (Duplicate)** |
| 33 | `TONGUE/Tongue_Vitamin_Deficiency_to_Suggested_Routine.csv` | 15 | 7 | 0 | utf-8 | **Used as Reference Lookup (Duplicate)** |
| 34 | `vitamin_deficiency_disease_dataset_20260123.csv` | 4000 | 34 | 0 | utf-8 | **Used for Training** |

---

## 2. Detailed File Profiles & Justifications

### 1. `EYES/Eyes_Symptoms_vs_Vitamin_Deficiency_Mapping.csv`
- **Size:** 5,782 bytes
- **Dimensions:** 15 rows × 9 columns
- **Encoding:** utf-8
- **Exact Duplicate Rows:** 0
- **Columns:** `Class_Label, Category, Vitamin_Deficiency, Associated_Vitamin, Key_Symptoms, Visible_Ocular_Signs, Common_Systemic_Symptoms, Risk_Factors, Severity_Level`
- **Decision:** **Used as Reference Lookup (Duplicate)**
- **Rationale:** Duplicate copy of MedBot regional mapping table placed in anatomical image folders. Curated copies in knowledge/curated/ are used.

### 2. `EYES/Eyes_Vitamin_Deficiency_to_Suggested_Routine.csv`
- **Size:** 6,848 bytes
- **Dimensions:** 10 rows × 7 columns
- **Encoding:** utf-8
- **Exact Duplicate Rows:** 0
- **Columns:** `Vitamin_Deficiency, Associated_Vitamin, Dietary_Recommendations, Suggested_Supplementation, Lifestyle_Routine, Follow_Up_Recommendation, Disclaimer`
- **Decision:** **Used as Reference Lookup (Duplicate)**
- **Rationale:** Duplicate copy of MedBot regional mapping table placed in anatomical image folders. Curated copies in knowledge/curated/ are used.

### 3. `EYES/Other_Ocular_Conditions/Glaucoma/G1020.csv`
- **Size:** 18,036 bytes
- **Dimensions:** 1020 rows × 2 columns
- **Encoding:** utf-8
- **Exact Duplicate Rows:** 0
- **Columns:** `imageID, binaryLabels`
- **Decision:** **Excluded**
- **Rationale:** Ophthalmic disease image ground truth / clinical metadata (G1020, HRDC). Excluded from tabular nutritional deficiency training.

### 4. `EYES/Other_Ocular_Conditions/Glaucoma/glaucoma.csv`
- **Size:** 14,906 bytes
- **Dimensions:** 650 rows × 5 columns
- **Encoding:** utf-8
- **Exact Duplicate Rows:** 0
- **Columns:** `Filename, ExpCDR, Eye, Set, Glaucoma`
- **Decision:** **Excluded**
- **Rationale:** Ophthalmic disease image ground truth / clinical metadata (G1020, HRDC). Excluded from tabular nutritional deficiency training.

### 5. `EYES/Other_Ocular_Conditions/Hypertensive_Retinopathy/1-Hypertensive Classification/1-Hypertensive Classification/2-Groundtruths/HRDC Hypertensive Classification Training Labels.csv`
- **Size:** 11,412 bytes
- **Dimensions:** 712 rows × 2 columns
- **Encoding:** utf-8
- **Exact Duplicate Rows:** 0
- **Columns:** `Image, Hypertensive`
- **Decision:** **Excluded**
- **Rationale:** Ophthalmic disease image ground truth / clinical metadata (G1020, HRDC). Excluded from tabular nutritional deficiency training.

### 6. `EYES/Other_Ocular_Conditions/Hypertensive_Retinopathy/2-Hypertensive Retinopathy Classification/2-Hypertensive Retinopathy Classification/2-Groundtruths/HRDC Hypertensive Retinopathy Classification Training Labels.csv`
- **Size:** 11,424 bytes
- **Dimensions:** 712 rows × 2 columns
- **Encoding:** utf-8
- **Exact Duplicate Rows:** 0
- **Columns:** `Image, Hypertensive Retinopathy`
- **Decision:** **Excluded**
- **Rationale:** Ophthalmic disease image ground truth / clinical metadata (G1020, HRDC). Excluded from tabular nutritional deficiency training.

### 7. `EYES/Other_Ocular_Conditions/Ocular Conditions/dataset.csv`
- **Size:** 155 bytes
- **Dimensions:** 9 rows × 3 columns
- **Encoding:** utf-8
- **Exact Duplicate Rows:** 0
- **Columns:** `set, class, count`
- **Decision:** **Excluded**
- **Rationale:** Ophthalmic disease image ground truth / clinical metadata (G1020, HRDC). Excluded from tabular nutritional deficiency training.

### 8. `HAIR/Hair_Symptoms_vs_Vitamin_Deficiency_Mapping.csv`
- **Size:** 13,046 bytes
- **Dimensions:** 32 rows × 10 columns
- **Encoding:** utf-8
- **Exact Duplicate Rows:** 0
- **Columns:** `Class_Label, Category, Subcategory, Vitamin_Deficiency, Associated_Nutrient, Key_Symptoms, Visible_Hair_Signs, Common_Systemic_Symptoms, Risk_Factors, Severity_Level`
- **Decision:** **Used as Reference Lookup (Duplicate)**
- **Rationale:** Duplicate copy of MedBot regional mapping table placed in anatomical image folders. Curated copies in knowledge/curated/ are used.

### 9. `HAIR/Hair_Vitamin_Deficiency_to_Suggested_Routine.csv`
- **Size:** 14,784 bytes
- **Dimensions:** 25 rows × 7 columns
- **Encoding:** utf-8
- **Exact Duplicate Rows:** 0
- **Columns:** `Vitamin_Deficiency, Associated_Nutrient, Dietary_Recommendations, Suggested_Supplementation, Lifestyle_Routine, Follow_Up_Recommendation, Disclaimer`
- **Decision:** **Used as Reference Lookup (Duplicate)**
- **Rationale:** Duplicate copy of MedBot regional mapping table placed in anatomical image folders. Curated copies in knowledge/curated/ are used.

### 10. `HAIR/Other/dataset_info.csv`
- **Size:** 4,493 bytes
- **Dimensions:** 98 rows × 4 columns
- **Encoding:** utf-8
- **Exact Duplicate Rows:** 0
- **Columns:** `id, image, mask, collage`
- **Decision:** **Excluded**
- **Rationale:** Hair image metadata catalog. Excluded from tabular deficiency modeling.

### 11. `LIPS/Lips_Symptoms_vs_Vitamin_Deficiency_Mapping.csv`
- **Size:** 6,050 bytes
- **Dimensions:** 14 rows × 9 columns
- **Encoding:** utf-8
- **Exact Duplicate Rows:** 0
- **Columns:** `Class_Label, Category, Vitamin_Deficiency, Associated_Nutrient, Key_Symptoms, Visible_Lip_Signs, Common_Systemic_Symptoms, Risk_Factors, Severity_Level`
- **Decision:** **Used as Reference Lookup (Duplicate)**
- **Rationale:** Duplicate copy of MedBot regional mapping table placed in anatomical image folders. Curated copies in knowledge/curated/ are used.

### 12. `LIPS/Lips_Vitamin_Deficiency_to_Suggested_Routine.csv`
- **Size:** 9,141 bytes
- **Dimensions:** 14 rows × 7 columns
- **Encoding:** utf-8
- **Exact Duplicate Rows:** 0
- **Columns:** `Vitamin_Deficiency, Associated_Nutrient, Dietary_Recommendations, Suggested_Supplementation, Lifestyle_Routine, Follow_Up_Recommendation, Disclaimer`
- **Decision:** **Used as Reference Lookup (Duplicate)**
- **Rationale:** Duplicate copy of MedBot regional mapping table placed in anatomical image folders. Curated copies in knowledge/curated/ are used.

### 13. `MedBot_datasets/Eyes_Symptoms_vs_Vitamin_Deficiency_Mapping.csv`
- **Size:** 5,782 bytes
- **Dimensions:** 15 rows × 9 columns
- **Encoding:** utf-8
- **Exact Duplicate Rows:** 0
- **Columns:** `Class_Label, Category, Vitamin_Deficiency, Associated_Vitamin, Key_Symptoms, Visible_Ocular_Signs, Common_Systemic_Symptoms, Risk_Factors, Severity_Level`
- **Decision:** **Used as Reference Lookup**
- **Rationale:** Curated regional symptom/routine mapping table. Used for deterministic clinical-rules lookup and crosswalk generation.

### 14. `MedBot_datasets/Eyes_Vitamin_Deficiency_to_Suggested_Routine.csv`
- **Size:** 6,848 bytes
- **Dimensions:** 10 rows × 7 columns
- **Encoding:** utf-8
- **Exact Duplicate Rows:** 0
- **Columns:** `Vitamin_Deficiency, Associated_Vitamin, Dietary_Recommendations, Suggested_Supplementation, Lifestyle_Routine, Follow_Up_Recommendation, Disclaimer`
- **Decision:** **Used as Reference Lookup**
- **Rationale:** Curated regional symptom/routine mapping table. Used for deterministic clinical-rules lookup and crosswalk generation.

### 15. `MedBot_datasets/Hair_Symptoms_vs_Vitamin_Deficiency_Mapping.csv`
- **Size:** 13,046 bytes
- **Dimensions:** 32 rows × 10 columns
- **Encoding:** utf-8
- **Exact Duplicate Rows:** 0
- **Columns:** `Class_Label, Category, Subcategory, Vitamin_Deficiency, Associated_Nutrient, Key_Symptoms, Visible_Hair_Signs, Common_Systemic_Symptoms, Risk_Factors, Severity_Level`
- **Decision:** **Used as Reference Lookup**
- **Rationale:** Curated regional symptom/routine mapping table. Used for deterministic clinical-rules lookup and crosswalk generation.

### 16. `MedBot_datasets/Hair_Vitamin_Deficiency_to_Suggested_Routine.csv`
- **Size:** 14,784 bytes
- **Dimensions:** 25 rows × 7 columns
- **Encoding:** utf-8
- **Exact Duplicate Rows:** 0
- **Columns:** `Vitamin_Deficiency, Associated_Nutrient, Dietary_Recommendations, Suggested_Supplementation, Lifestyle_Routine, Follow_Up_Recommendation, Disclaimer`
- **Decision:** **Used as Reference Lookup**
- **Rationale:** Curated regional symptom/routine mapping table. Used for deterministic clinical-rules lookup and crosswalk generation.

### 17. `MedBot_datasets/Lips_Symptoms_vs_Vitamin_Deficiency_Mapping.csv`
- **Size:** 6,050 bytes
- **Dimensions:** 14 rows × 9 columns
- **Encoding:** utf-8
- **Exact Duplicate Rows:** 0
- **Columns:** `Class_Label, Category, Vitamin_Deficiency, Associated_Nutrient, Key_Symptoms, Visible_Lip_Signs, Common_Systemic_Symptoms, Risk_Factors, Severity_Level`
- **Decision:** **Used as Reference Lookup**
- **Rationale:** Curated regional symptom/routine mapping table. Used for deterministic clinical-rules lookup and crosswalk generation.

### 18. `MedBot_datasets/Lips_Vitamin_Deficiency_to_Suggested_Routine.csv`
- **Size:** 9,141 bytes
- **Dimensions:** 14 rows × 7 columns
- **Encoding:** utf-8
- **Exact Duplicate Rows:** 0
- **Columns:** `Vitamin_Deficiency, Associated_Nutrient, Dietary_Recommendations, Suggested_Supplementation, Lifestyle_Routine, Follow_Up_Recommendation, Disclaimer`
- **Decision:** **Used as Reference Lookup**
- **Rationale:** Curated regional symptom/routine mapping table. Used for deterministic clinical-rules lookup and crosswalk generation.

### 19. `MedBot_datasets/MedNourish_Symptom_Keywords_vs_Vitamin_Deficiency_Mapping.csv`
- **Size:** 13,114 bytes
- **Dimensions:** 116 rows × 5 columns
- **Encoding:** utf-8
- **Exact Duplicate Rows:** 0
- **Columns:** `Class_Label, Body_Region, Category, Vitamin_Deficiency, Symptom_Keywords`
- **Decision:** **Used for Training & Reference**
- **Rationale:** Master canonical mapping table (116 rows). Used for reference-table keyword-to-nutrient ML model and deterministic symptom lookup.

### 20. `MedBot_datasets/Nails_Symptoms_vs_Vitamin_Deficiency_Mapping.csv`
- **Size:** 6,817 bytes
- **Dimensions:** 16 rows × 9 columns
- **Encoding:** utf-8
- **Exact Duplicate Rows:** 0
- **Columns:** `Class_Label, Category, Vitamin_Deficiency, Associated_Nutrient, Key_Symptoms, Visible_Nail_Signs, Common_Systemic_Symptoms, Risk_Factors, Severity_Level`
- **Decision:** **Used as Reference Lookup**
- **Rationale:** Curated regional symptom/routine mapping table. Used for deterministic clinical-rules lookup and crosswalk generation.

### 21. `MedBot_datasets/Nails_Vitamin_Deficiency_to_Suggested_Routine.csv`
- **Size:** 7,772 bytes
- **Dimensions:** 12 rows × 7 columns
- **Encoding:** utf-8
- **Exact Duplicate Rows:** 0
- **Columns:** `Vitamin_Deficiency, Associated_Nutrient, Dietary_Recommendations, Suggested_Supplementation, Lifestyle_Routine, Follow_Up_Recommendation, Disclaimer`
- **Decision:** **Used as Reference Lookup**
- **Rationale:** Curated regional symptom/routine mapping table. Used for deterministic clinical-rules lookup and crosswalk generation.

### 22. `MedBot_datasets/Skin_Symptoms_vs_Vitamin_Deficiency_Mapping.csv`
- **Size:** 9,808 bytes
- **Dimensions:** 23 rows × 9 columns
- **Encoding:** utf-8
- **Exact Duplicate Rows:** 0
- **Columns:** `Class_Label, Category, Vitamin_Deficiency, Associated_Nutrient, Key_Symptoms, Visible_Skin_Signs, Common_Systemic_Symptoms, Risk_Factors, Severity_Level`
- **Decision:** **Used as Reference Lookup**
- **Rationale:** Curated regional symptom/routine mapping table. Used for deterministic clinical-rules lookup and crosswalk generation.

### 23. `MedBot_datasets/Skin_Vitamin_Deficiency_to_Suggested_Routine.csv`
- **Size:** 5,193 bytes
- **Dimensions:** 7 rows × 7 columns
- **Encoding:** utf-8
- **Exact Duplicate Rows:** 0
- **Columns:** `Vitamin_Deficiency, Associated_Nutrient, Dietary_Recommendations, Suggested_Supplementation, Lifestyle_Routine, Follow_Up_Recommendation, Disclaimer`
- **Decision:** **Used as Reference Lookup**
- **Rationale:** Curated regional symptom/routine mapping table. Used for deterministic clinical-rules lookup and crosswalk generation.

### 24. `MedBot_datasets/Tongue_Symptoms_vs_Vitamin_Deficiency_Mapping.csv`
- **Size:** 6,974 bytes
- **Dimensions:** 16 rows × 9 columns
- **Encoding:** utf-8
- **Exact Duplicate Rows:** 0
- **Columns:** `Class_Label, Category, Vitamin_Deficiency, Associated_Nutrient, Key_Symptoms, Visible_Tongue_Signs, Common_Systemic_Symptoms, Risk_Factors, Severity_Level`
- **Decision:** **Used as Reference Lookup**
- **Rationale:** Curated regional symptom/routine mapping table. Used for deterministic clinical-rules lookup and crosswalk generation.

### 25. `MedBot_datasets/Tongue_Vitamin_Deficiency_to_Suggested_Routine.csv`
- **Size:** 9,515 bytes
- **Dimensions:** 15 rows × 7 columns
- **Encoding:** utf-8
- **Exact Duplicate Rows:** 0
- **Columns:** `Vitamin_Deficiency, Associated_Nutrient, Dietary_Recommendations, Suggested_Supplementation, Lifestyle_Routine, Follow_Up_Recommendation, Disclaimer`
- **Decision:** **Used as Reference Lookup**
- **Rationale:** Curated regional symptom/routine mapping table. Used for deterministic clinical-rules lookup and crosswalk generation.

### 26. `NAILS/Nails_Symptoms_vs_Vitamin_Deficiency_Mapping.csv`
- **Size:** 6,817 bytes
- **Dimensions:** 16 rows × 9 columns
- **Encoding:** utf-8
- **Exact Duplicate Rows:** 0
- **Columns:** `Class_Label, Category, Vitamin_Deficiency, Associated_Nutrient, Key_Symptoms, Visible_Nail_Signs, Common_Systemic_Symptoms, Risk_Factors, Severity_Level`
- **Decision:** **Used as Reference Lookup (Duplicate)**
- **Rationale:** Duplicate copy of MedBot regional mapping table placed in anatomical image folders. Curated copies in knowledge/curated/ are used.

### 27. `NAILS/Nails_Vitamin_Deficiency_to_Suggested_Routine.csv`
- **Size:** 7,772 bytes
- **Dimensions:** 12 rows × 7 columns
- **Encoding:** utf-8
- **Exact Duplicate Rows:** 0
- **Columns:** `Vitamin_Deficiency, Associated_Nutrient, Dietary_Recommendations, Suggested_Supplementation, Lifestyle_Routine, Follow_Up_Recommendation, Disclaimer`
- **Decision:** **Used as Reference Lookup (Duplicate)**
- **Rationale:** Duplicate copy of MedBot regional mapping table placed in anatomical image folders. Curated copies in knowledge/curated/ are used.

### 28. `SKIN/OTHER/balanced_dataset.csv`
- **Size:** 33,847,532 bytes
- **Dimensions:** 245442 rows × 2 columns
- **Encoding:** utf-8
- **Exact Duplicate Rows:** 463
- **Columns:** `image_path, category`
- **Decision:** **Excluded**
- **Rationale:** Dermatology image classification labels / metadata (HAM10000/ISIC skin lesion subset). Excluded from tabular deficiency models to prevent domain confusion.

### 29. `SKIN/OTHER/balanced_dataset/balanced_dataset.csv`
- **Size:** 33,847,532 bytes
- **Dimensions:** 245442 rows × 2 columns
- **Encoding:** utf-8
- **Exact Duplicate Rows:** 463
- **Columns:** `image_path, category`
- **Decision:** **Excluded**
- **Rationale:** Dermatology image classification labels / metadata (HAM10000/ISIC skin lesion subset). Excluded from tabular deficiency models to prevent domain confusion.

### 30. `SKIN/Skin_Symptoms_vs_Vitamin_Deficiency_Mapping.csv`
- **Size:** 9,808 bytes
- **Dimensions:** 23 rows × 9 columns
- **Encoding:** utf-8
- **Exact Duplicate Rows:** 0
- **Columns:** `Class_Label, Category, Vitamin_Deficiency, Associated_Nutrient, Key_Symptoms, Visible_Skin_Signs, Common_Systemic_Symptoms, Risk_Factors, Severity_Level`
- **Decision:** **Used as Reference Lookup (Duplicate)**
- **Rationale:** Duplicate copy of MedBot regional mapping table placed in anatomical image folders. Curated copies in knowledge/curated/ are used.

### 31. `SKIN/Skin_Vitamin_Deficiency_to_Suggested_Routine.csv`
- **Size:** 5,193 bytes
- **Dimensions:** 7 rows × 7 columns
- **Encoding:** utf-8
- **Exact Duplicate Rows:** 0
- **Columns:** `Vitamin_Deficiency, Associated_Nutrient, Dietary_Recommendations, Suggested_Supplementation, Lifestyle_Routine, Follow_Up_Recommendation, Disclaimer`
- **Decision:** **Used as Reference Lookup (Duplicate)**
- **Rationale:** Duplicate copy of MedBot regional mapping table placed in anatomical image folders. Curated copies in knowledge/curated/ are used.

### 32. `TONGUE/Tongue_Symptoms_vs_Vitamin_Deficiency_Mapping.csv`
- **Size:** 6,974 bytes
- **Dimensions:** 16 rows × 9 columns
- **Encoding:** utf-8
- **Exact Duplicate Rows:** 0
- **Columns:** `Class_Label, Category, Vitamin_Deficiency, Associated_Nutrient, Key_Symptoms, Visible_Tongue_Signs, Common_Systemic_Symptoms, Risk_Factors, Severity_Level`
- **Decision:** **Used as Reference Lookup (Duplicate)**
- **Rationale:** Duplicate copy of MedBot regional mapping table placed in anatomical image folders. Curated copies in knowledge/curated/ are used.

### 33. `TONGUE/Tongue_Vitamin_Deficiency_to_Suggested_Routine.csv`
- **Size:** 9,515 bytes
- **Dimensions:** 15 rows × 7 columns
- **Encoding:** utf-8
- **Exact Duplicate Rows:** 0
- **Columns:** `Vitamin_Deficiency, Associated_Nutrient, Dietary_Recommendations, Suggested_Supplementation, Lifestyle_Routine, Follow_Up_Recommendation, Disclaimer`
- **Decision:** **Used as Reference Lookup (Duplicate)**
- **Rationale:** Duplicate copy of MedBot regional mapping table placed in anatomical image folders. Curated copies in knowledge/curated/ are used.

### 34. `vitamin_deficiency_disease_dataset_20260123.csv`
- **Size:** 742,012 bytes
- **Dimensions:** 4000 rows × 34 columns
- **Encoding:** utf-8
- **Exact Duplicate Rows:** 0
- **Columns:** `age, gender, bmi, smoking_status, alcohol_consumption, exercise_level, diet_type, sun_exposure, income_level, latitude_region, vitamin_a_percent_rda, vitamin_c_percent_rda, vitamin_d_percent_rda, vitamin_e_percent_rda, vitamin_b12_percent_rda, folate_percent_rda, calcium_percent_rda, iron_percent_rda, hemoglobin_g_dl, serum_vitamin_d_ng_ml, serum_vitamin_b12_pg_ml, serum_folate_ng_ml, symptoms_count, symptoms_list, has_night_blindness, has_fatigue, has_bleeding_gums, has_bone_pain, has_muscle_weakness, has_numbness_tingling, has_memory_problems, has_pale_skin, disease_diagnosis, has_multiple_deficiencies`
- **Decision:** **Used for Training**
- **Rationale:** Main synthetic clinical tabular dataset (4,000 rows x 34 cols). Used for tabular ML benchmarking (XGBoost/LightGBM) with & without serum lab features.

