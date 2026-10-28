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

1. **EYES (46,614 total files):**
   - In preliminary audits, `datasets/EYES/Other_Ocular_Conditions/Other/` was loosely categorized as 'other' files.
   - Comprehensive file extension and magic-byte inspection reveals these contain **microscopic blood smear cell images** (`basophil`, `eosinophil`, `erythroblast`, `ig`, `lymphocyte`, `monocyte`, `neutrophil`, `platelet`) with `.jpg` extensions along with optic nerve/cup segmentation masks, annotation files, and 1 Jupyter notebook (`eye-diseases-classification.ipynb`).
   - Exact breakdown of EYES: **41,845 images**, **3,080 masks**, **1,685 annotations**, **1 notebook**, **3 other** = **46,614 total files**.

2. **TONGUE (40,751 total files):**
   - The root clinical folders (`Diabetes`, `Healthy`, `OralCancer`, `Pre Diabetes`) contain 428 clinical tongue images.
   - The large subfolder `shezhen datasets` contains Traditional Chinese Medicine tongue segmentations in 3 formats: `shezhenv3-coco`, `shezhenv3-txt`, and `shezhenv3-xml` totaling 40,322 files.
   - Exact breakdown of TONGUE: **20,585 images**, **20,165 annotations**, **0 masks**, **0 notebooks**, **1 other** = **40,751 total files**.

3. **Total Corpus (394,480 total files):**
   - Historical estimates (such as ~372,536 images) loosely lumped masks, segmentation collages, and blood smears together without distinguishing masks or annotations.
   - Exact physical file audit across all 8 directories + root files is exactly **394,480 files**:
     * **364,292 genuine image files** (ocular, tongue, hair, nail, skin, lip, and multi-vitamin images)
     * **8,244 mask / segmentation images** (facial lip masks, hair masks, ocular glaucoma masks)
     * **21,936 annotation / label / metadata files** (COCO JSON, YOLO TXT, Pascal VOC XML, CSVs)
     * **4 Jupyter notebooks**
     * **4 other files** (`DATASET_STRUCTURE.txt`, etc.)

