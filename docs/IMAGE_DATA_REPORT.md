# MedNourish — Computer Vision Image Dataset Audit & Manifest Report

**Report Date:** 2026-10-14  
**Governing Milestone:** Phase 3.3 Stage 3 (Image Dataset Analysis & Manifests)  
**Dataset Source Archive:** `C:\Users\USER\Desktop\MedNourish\datasets`  

This document reports the empirical inventory, deduplication, quality filtering, 
class threshold gating (>= 100 images), and group-aware 70/15/15 splits across all 7 vision models.

---

## 1. Executive Summary Table

| Model | Usable Classes | Total Retained | Train (70%) | Val (15%) | Test (15%) | Exact Dups Removed | Near-Dups Clustered | Quality Rejections |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **`combined`** | 7 | 3776 | 2642 | 566 | 568 | 3654 | 184 | 52 |
| **`eyes`** | 3 | 1800 | 1260 | 270 | 270 | 32 | 393 | 10 |
| **`hair`** | 2 | 717 | 501 | 107 | 109 | 1 | 134 | 0 |
| **`lips`** | 1 | 600 | 420 | 90 | 90 | 79 | 43 | 0 |
| **`nails`** | 2 | 726 | 508 | 108 | 110 | 31 | 23 | 179 |
| **`skin`** | 2 | 1200 | 840 | 180 | 180 | 24 | 11 | 0 |
| **`tongue`** | 4 | 977 | 683 | 145 | 149 | 23 | 24 | 0 |

---

## 2. Model Profiles & Gating Decisions

### Model: `COMBINED`
- **Dataset Root Folder:** `dataset`
- **Configured Class Cap:** 600 images/class
- **Retained Classes (7):** `Vitamin_A_Deficiency, Vitamin_B_Complex_Deficiency, Vitamin_B12_Deficiency, Vitamin_B3_Deficiency, Vitamin_B9_Deficiency, Vitamin_D_Deficiency, Other_Nutrient_Deficiency`
- **Class Count Breakdown (Initial vs Cleaned):**
  * `Vitamin_A_Deficiency`: 1,200 raw -> 600 cleaned
  * `Vitamin_B_Complex_Deficiency`: 1,127 raw -> 600 cleaned
  * `Vitamin_B12_Deficiency`: 1,200 raw -> 600 cleaned
  * `Vitamin_B2_Deficiency`: 656 raw -> 34 cleaned
  * `Vitamin_B3_Deficiency`: 618 raw -> 354 cleaned
  * `Vitamin_B9_Deficiency`: 840 raw -> 422 cleaned
  * `Vitamin_C_Deficiency`: 664 raw -> 82 cleaned
  * `Vitamin_D_Deficiency`: 1,200 raw -> 600 cleaned
  * `Vitamin_E_Deficiency`: 692 raw -> 51 cleaned
  * `Vitamin_K_Deficiency`: 690 raw -> 61 cleaned
  * `Other_Nutrient_Deficiency`: 987 raw -> 600 cleaned
- **Dropped / Excluded Classes (< 100 usable images):**
  * **`Vitamin_B2_Deficiency`**: Under minimum support threshold (usable=34 < 100)
  * **`Vitamin_C_Deficiency`**: Under minimum support threshold (usable=82 < 100)
  * **`Vitamin_E_Deficiency`**: Under minimum support threshold (usable=51 < 100)
  * **`Vitamin_K_Deficiency`**: Under minimum support threshold (usable=61 < 100)

### Model: `EYES`
- **Dataset Root Folder:** `EYES`
- **Configured Class Cap:** 600 images/class
- **Retained Classes (3):** `Normal, Vitamin_A_Deficiency, Other_Non_Nutritional`
- **Class Count Breakdown (Initial vs Cleaned):**
  * `Normal`: 1,200 raw -> 600 cleaned
  * `Vitamin_A_Deficiency`: 841 raw -> 600 cleaned
  * `Other_Non_Nutritional`: 1,200 raw -> 600 cleaned
- **Dropped / Excluded Classes (< 100 usable images):**
  * **`Nutritional_Optic_Conditions`**: Dropped due to insufficient sample count (< 100 usable images: 22 images)

### Model: `HAIR`
- **Dataset Root Folder:** `HAIR`
- **Configured Class Cap:** 600 images/class
- **Retained Classes (2):** `Normal, Other_Non_Nutritional`
- **Class Count Breakdown (Initial vs Cleaned):**
  * `Normal`: 1,200 raw -> 600 cleaned
  * `Other_Non_Nutritional`: 196 raw -> 117 cleaned
- **Dropped / Excluded Classes (< 100 usable images):**
  * **`Alopecia`**: Dropped due to insufficient sample count (< 100 usable images: 31 images)
  * **`Corkscrew_Hair`**: Dropped due to insufficient sample count (< 100 usable images: 19 images)
  * **`Sparse_Hair`**: Dropped due to insufficient sample count (< 100 usable images: 13 images)

### Model: `LIPS`
- **Dataset Root Folder:** `LIPS`
- **Configured Class Cap:** 600 images/class
- **Retained Classes (1):** `Normal`
- **Class Count Breakdown (Initial vs Cleaned):**
  * `Normal`: 1,200 raw -> 600 cleaned
- **Dropped / Excluded Classes (< 100 usable images):**
  * **`NON_NUTRITIONAL`**: Dropped due to insufficient sample count (< 100 usable images: 91 images)
  * **`NUTRITIONAL`**: Dropped due to insufficient sample count (< 100 usable images: 90 images)

### Model: `NAILS`
- **Dataset Root Folder:** `NAILS`
- **Configured Class Cap:** 600 images/class
- **Retained Classes (2):** `Nutritional, Other_Non_Nutritional`
- **Class Count Breakdown (Initial vs Cleaned):**
  * `Nutritional`: 158 raw -> 126 cleaned
  * `Other_Non_Nutritional`: 1,200 raw -> 600 cleaned
- **Dropped / Excluded Classes (< 100 usable images):**
  * **`NORMAL`**: Dropped due to insufficient sample count (< 100 usable images: 60 images)

### Model: `SKIN`
- **Dataset Root Folder:** `SKIN`
- **Configured Class Cap:** 600 images/class
- **Retained Classes (2):** `Normal, Other_Non_Nutritional`
- **Class Count Breakdown (Initial vs Cleaned):**
  * `Normal`: 1,200 raw -> 600 cleaned
  * `Vitamin_B3_Pellagra`: 111 raw -> 94 cleaned
  * `Other_Non_Nutritional`: 1,200 raw -> 600 cleaned
- **Dropped / Excluded Classes (< 100 usable images):**
  * **`ZINC`**: Dropped due to insufficient sample count (< 100 usable images: 97 images)
  * **`VITAMIN_C`**: Dropped due to insufficient sample count (< 100 usable images: 88 images)
  * **`VITAMIN_A`**: Dropped due to insufficient sample count (< 100 usable images: 46 images)
  * **`BIOTIN`**: Dropped due to insufficient sample count (< 100 usable images: 40 images)
  * **`PROTEIN_ENERGY_MALNUTRITION`**: Dropped due to insufficient sample count (< 100 usable images: 35 images)
  * **`Vitamin_B3_Pellagra`**: Under minimum support threshold (usable=94 < 100)

### Model: `TONGUE`
- **Dataset Root Folder:** `TONGUE`
- **Configured Class Cap:** 600 images/class
- **Retained Classes (4):** `Healthy, Diabetes, OralCancer, Other_TCM_Tongue`
- **Class Count Breakdown (Initial vs Cleaned):**
  * `Healthy`: 113 raw -> 113 cleaned
  * `Diabetes`: 160 raw -> 160 cleaned
  * `OralCancer`: 131 raw -> 104 cleaned
  * `Other_TCM_Tongue`: 1,200 raw -> 600 cleaned
- **Dropped / Excluded Classes (< 100 usable images):**
  * **`Pre Diabetes`**: Dropped due to insufficient sample count (< 100 usable images: 24 images)

---

## 3. Class Semantics & True Composition (What the Classes Really Mean)

> [!WARNING]
> **Dataset-Group Classifiers, Not Deficiency Detectors**
> The vision models classify heterogeneous dataset collections and source photography groups, NOT clinical pathology. 

1. **EYES — `Other_Non_Nutritional` (600 images) [⚠️ Likely Dataset-Source Shortcut]:**
   - Source: `datasets/EYES/Other_Ocular_Conditions/Glaucoma` (fundus photography / optic disc images).
   - Normal: 600 close-up eyelid/cornea images.
   - Vitamin_A_Deficiency: 600 Bitot spots / xerophthalmia images.
   - **Shortcut Risk:** The 100% test accuracy is an artifact of the network separating retinal fundus camera captures from external eyelid photography.

2. **SKIN — `Other_Non_Nutritional` (600 images) [⚠️ Likely Dataset-Source Shortcut]:**
   - Source: `datasets/SKIN/OTHER/balanced_dataset` (web-scraped dermatology repository).
   - **NO Nutritional Class:** All nutritional deficiency skin classes (`ZINC`: 97, `VITAMIN_C`: 88, `VITAMIN_A`: 46, `BIOTIN`: 40, `PEM`: 35, `Vitamin_B3_Pellagra`: 94) were dropped because each had fewer than 100 usable images.
   - **Shortcut Risk:** Model accuracy (98.33%) reflects high-resolution web dermatology crops vs normal amateur skin shots.

3. **HAIR — `Normal` vs `Other_Non_Nutritional` (109 test images):**
   - **NO Nutritional Class:** All nutritional deficiency hair classes (`Alopecia`: 31, `Corkscrew_Hair`: 19, `Sparse_Hair`: 13) were dropped (< 100 images). This model simply separates generic scalp hair from non-nutritional scalp conditions.

4. **LIPS — NO Trained Model:**
   - Only `Normal` (600 images) passed the 100-image threshold. `NON_NUTRITIONAL` (91 images) and `NUTRITIONAL` (90 images) both failed the gate. Hence, zero lips models exist.

5. **NAILS — `Nutritional` (126 images) vs `Other_Non_Nutritional` (600 images):**
   - `Other_Non_Nutritional` pools 302 images from `NON_NUTRITIONAL` (onychomycosis, trauma) and 298 from `OTHER` (dystrophies).
   - `Nutritional` contains 126 koilonychia / iron deficiency images.

6. **TONGUE — `Other_TCM_Tongue` (600 images):**
   - Source: `datasets/TONGUE/shezhen datasets/shezhenv3-coco` (Traditional Chinese Medicine tongue segmentation dataset).
   - Accompanies `Healthy` (113), `Diabetes` (160), and `OralCancer` (104).
   - Reflects systemic disease and TCM dataset cohorts rather than isolated micro-nutrient deficiency detection.

7. **COMBINED — Dropped B2/C/E/K & `Other_Nutrient_Deficiency` (600 images):**
   - Dropped: `Vitamin_B2_Deficiency` (34), `Vitamin_C_Deficiency` (82), `Vitamin_E_Deficiency` (51), `Vitamin_K_Deficiency` (61).
   - `Other_Nutrient_Deficiency`: 600 images from `zinc, iron, biotin, or protein deficiency` containing miscellaneous clinical images (tinea, periungual warts, mucous cysts, fissures).

---

## 4. Known Methodological Risks & Clinical Disclaimers

1. **Source-per-Class Shortcut Learning:**
   - Pathological and normal image subsets originate from distinct open-source clinical repositories 
     with differing aspect ratios, lighting temperatures, background colors, and sensor characteristics.
   - Neural networks risk learning source sensor artifacts rather than physiological pathology.
2. **Anatomical Overlap and Diagnostic Specificity:**
   - Physical signs such as follicular hyperkeratosis, atrophic glossitis, or brittle nails are not pathognomonic 
     for a single micronutrient deficiency; overlapping systemic etiology is ubiquitous in clinical medicine.
3. **Strict Academic Demo Scope:**
   - All vision models are educational prototypes demonstrating computer-vision engineering feasibility. 
   - Zero clinical or diagnostic authority is claimed or permitted under project guidelines.


