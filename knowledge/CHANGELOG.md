# MEDNOURISH Knowledge Base Changelog

All modifications to reference knowledge files follow `Rules.md` (DAT-04) and `Architecture.md` Section 5.3.
Original datasets in `C:\Users\USER\Desktop\MedNourish\datasets` are read-only and byte-identical (GR-01).
All curated files reside in `knowledge/curated/`.

---

## [Tier 1 Mechanical Repairs] — 2026-10-12

### 1. `Hair_Symptoms_vs_Vitamin_Deficiency_Mapping.csv`
- **Location:** `knowledge/curated/Hair_Symptoms_vs_Vitamin_Deficiency_Mapping.csv`
- **Line 31 (Row index 30):**
  - **Issue:** Unquoted commas inside `Structural (Genetic, Rarely Metabolic)` and `Rarely Copper-Related (e.g., Menkes disease in infants)` caused CSV splitting into 12 columns instead of the expected 10 columns (`Class_Label`, `Category`, `Subcategory`, `Vitamin_Deficiency`, `Associated_Nutrient`, `Key_Symptoms`, `Visible_Hair_Signs`, `Common_Systemic_Symptoms`, `Risk_Factors`, `Severity_Level`).
  - **Action:** Enclosed the two fields in standard double quotes.
  - **Result:** Successfully parses to exactly 10 columns with all values preserved.

### 2. `Hair_Vitamin_Deficiency_to_Suggested_Routine.csv`
- **Location:** `knowledge/curated/Hair_Vitamin_Deficiency_to_Suggested_Routine.csv`
- **Line 24 (Row index 23):**
  - **Issue:** Unquoted commas in `Structural (Genetic, Rarely Metabolic)` and `Rarely Copper-Related (e.g., Menkes disease in infants)` caused row splitting into 9 columns instead of the expected 7 columns (`Vitamin_Deficiency`, `Associated_Nutrient`, `Dietary_Recommendations`, `Suggested_Supplementation`, `Lifestyle_Routine`, `Follow_Up_Recommendation`, `Disclaimer`).
  - **Action:** Enclosed the two fields in standard double quotes.
  - **Result:** Successfully parses to exactly 7 columns.

---

## [Content Safety Flags (OD-02, SAF-02, SAF-10, SAF-16)] — 2026-10-12

The reference tables contain entries referencing pediatric conditions and supplement/drug recommendations:
- **Pediatric References:** 22 instances across mapping and routine tables (e.g., Menkes disease in infants).
  - **Policy (`SAF-10`, `C-01`):** MedNourish is strictly for adults aged 18+. Child/infant-specific rows are excluded from user-facing search and matching results.
- **Supplementation & Treatment References:** 31 instances across routines.
  - **Policy (`SAF-02`, `SAF-16`, `C-17`):** Unreviewed supplement dosages, drug treatments (e.g., copper-histidine therapy), and urgency timeframes are flagged as unreviewed drafts and excluded from client displays.
