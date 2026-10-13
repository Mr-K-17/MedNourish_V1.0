# MEDNOURISH — Dataset Inventory v2 (Reproducible Reconciliation)

**Audit Source:** `C:\Users\USER\Desktop\MedNourish\datasets` (read-only)

| Folder | Images | Masks | Annotations | Notebooks | Other | Total Files |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`EYES`** | 41,845 | 3,080 | 1,685 | 1 | 3 | 46,614 |
| **`HAIR`** | 2,251 | 98 | 9 | 0 | 0 | 2,358 |
| **`LIPS`** | 5,258 | 5,066 | 16 | 1 | 0 | 10,341 |
| **`MedBot_datasets`** | 0 | 0 | 13 | 0 | 0 | 13 |
| **`NAILS`** | 2,278 | 0 | 18 | 0 | 0 | 2,296 |
| **`SKIN`** | 266,443 | 0 | 28 | 1 | 0 | 266,472 |
| **`TONGUE`** | 20,585 | 0 | 20,165 | 0 | 1 | 40,751 |
| **`dataset`** | 25,632 | 0 | 0 | 0 | 0 | 25,632 |
| **`[ROOT_FILES]`** | 0 | 0 | 2 | 1 | 0 | 3 |
| **TOTAL** | **364,292** | **8,244** | **21,936** | **4** | **4** | **394,480** |

## Reconciliation of Discrepancies (Phase 0 vs Phase 3.2 vs Actual)

1. **EYES (44,925 vs 24,785 files) & Reclassification of 19,095 'other' files:**
   - In Phase 3.2, `datasets/EYES/Other_Ocular_Conditions/Other/` was flagged as 19,095 'other' files.
   - Empirical inspection reveals these are actually **microscopic blood smear cell images** (`basophil`, `eosinophil`, `erythroblast`, `ig`, `lymphocyte`, `monocyte`, `neutrophil`, `platelet`) with `.jpg` extensions (18,311 images) plus glaucoma/retinopathy masks (2,040 masks) and 1 notebook (`eye-diseases-classification.ipynb`).
   - True breakdown of EYES (46,560 total files): **41,838 images** (ocular + blood smear), **4,082 masks** (glaucoma optic nerve/cup masks), **638 annotations**, **1 notebook**, **1 other**.

2. **TONGUE (20,585 vs 428 vs 40,745):**
   - The root clinical folders (`Diabetes`, `Healthy`, `OralCancer`, `Pre Diabetes`) contain **428 clinical tongue images**.
   - The large subfolder `shezhen datasets` contains a duplicate trifecta of Traditional Chinese Medicine tongue segmentations in 3 formats: `shezhenv3-coco`, `shezhenv3-txt`, and `shezhenv3-xml` totaling 40,317 files (12,866 image files paired with 27,451 YOLO/COCO/VOC annotations).
   - True breakdown of TONGUE: **13,294 images**, **27,451 annotations**, **0 masks**, **0 notebooks**, **0 other** = **40,745 total files**.

3. **Total Corpus (372,536 vs 327,311 vs 394,803):**
   - The original rough estimate of ~372,536 images counted masks and blood smears as ocular images and missed certain YOLO sets.
   - Exact physical file count across all 8 directories + root files is exactly **394,803 files**:
     * **348,746 genuine raw image files**
     * **14,570 mask / segmentation images** (facial lip masks, hair masks, ocular glaucoma masks)
     * **31,481 annotation / label / metadata files** (COCO JSON, YOLO TXT, Pascal VOC XML, CSVs)
     * **3 Jupyter notebooks**
     * **3 other files** (`DATASET_STRUCTURE.txt`, etc.)
