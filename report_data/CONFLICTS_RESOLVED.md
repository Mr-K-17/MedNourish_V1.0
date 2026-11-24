# Conflicts and Discrepancies Resolution Record

This document records the empirical resolution of all technical conflicts and discrepancies between early design specifications, intermediate audit documents, and the final production implementation in `MedNourish-Dev` (commit `51865759`). Per Rule 6, where planning documents disagree with code, the **CODE wins**.

---

### 1. Demo Risk-Band Thresholds
- **Question:** Does the system use High >= 60%, Moderate 30–59% (`SCORING_SPEC.md`) or Low < 34, Moderate 34–66, High >= 67 (`MEDNOURISH_AUDIT_PROGRESS.md`)?
- **Empirical Resolution:** The final codebase strictly uses **High >= 60.0%**, **Moderate 30.0% – 59.9%**, and **Low < 30.0%**.
- **Code Evidence:** 
  - `backend/app/services/scoring_service.py` lines 31–41:
    ```python
    THRESHOLD_HIGH = 60.0
    THRESHOLD_MODERATE = 30.0
    def calculate_risk_band(pct: float) -> str:
        if pct >= THRESHOLD_HIGH: return "High"
        elif pct >= THRESHOLD_MODERATE: return "Moderate"
        return "Low"
    ```
- **Superseded Document:** `MEDNOURISH_AUDIT_PROGRESS.md` (which referenced an earlier three-way equal split proposal).

---

### 2. Backend Test Count Today
- **Question:** Are there 98 passed + 1 skipped tests or 115 tests?
- **Empirical Resolution:** Running `pytest` today yields exactly **115 passed, 0 skipped, 0 failed** in `backend/tests/`.
- **Command Evidence:** `pytest tests -q` executed in `backend/.venv` (Python 3.14.8) completed with:
  `115 passed, 174 warnings in 166.30s (0:02:46)`.
- **Reason for Difference:** Earlier documentation (such as `README.md` at S-048) reflected the test count prior to Phase 6 / CarePlan v3 meal planner additions (`test_meal_plan.py` added 17 new tests covering nutritional guidance, dietary profiles, vegan filtering, and `.ics` generation).

---

### 3. Image Corpus and Physical File Counts
- **Question:** Is the dataset 372,536 images (Phase 0 estimate) or 364,292 images / 394,480 total files (`DATASET_INVENTORY_v2.md`)?
- **Empirical Resolution:** The exact physical count confirmed by file-level enumeration across `C:\Users\USER\Desktop\MedNourish\datasets` is:
  - **Total Physical Files:** **394,480**
  - **Genuine Image Files:** **364,292**
  - **Segmentation / Region Masks:** **8,244**
  - **Label / Annotation Files:** **21,936** (COCO JSON, YOLO TXT, Pascal VOC XML)
  - **Jupyter Notebooks:** **4**
  - **Other Files:** **4**
- **Evidence Path:** `docs/DATASET_INVENTORY_v2.md`.
- **Reason for Difference:** The early 372,536 estimate loosely grouped masks, blood cell images from ocular subfolders, and annotation files as generic images.

---

### 4. Vision Models: Final Architecture & Support Gate
- **Question:** Which vision model version is final (v1 vs v2)? What support gate was used? Does `lips` exist? How many classes in `combined`?
- **Empirical Resolution:** 
  - **Final Version:** **v2** (trained and verified in Phase 3.3, Stage 3).
  - **Support Gate:** **>= 40 usable images per class** (lowered from v1's >= 100 gate to enable clinical coverage for lips).
  - **Lips Model:** **YES, `lips` exists in v2** (3 classes: `Cheilitis`, `Herpes_Labialis`, `Normal`).
  - **Combined Model Classes:** Exactly **10 classes** in v2 (`Angular_Cheilitis`, `Aphthous_Ulcer`, `Cheilitis`, `Eye_Blepharitis`, `Eye_Conjunctivitis`, `Eye_Normal`, `Hair_Alopecia_Areata`, `Hair_Normal`, `Nail_Koilonychia`, `Skin_Normal`).
- **Code & Artifact Evidence:**
  - `ml/artifacts/v2/vision_v2_summary.json`
  - `ml/class_maps/` (all 7 region YAMLs + `combined.yaml`)
  - `backend/app/services/medscan_service.py` lines 42–51.

---

### 5. Generative AI & LLM Status
- **Question:** Does the final system still say "no LLM"? Is any LLM used anywhere? What does NurseBot use?
- **Empirical Resolution:** **Zero Generative LLMs are used.** MEDNOURISH is 100% deterministic and rule-governed in its user-facing advice:
  - **NurseBot:** Uses a deterministic intent router (`backend/app/services/nursebot_ai_service.py`) with regex keyword matching for emergency triage and application FAQ.
  - **Health Information:** Informational questions are answered via `WebAnswerService` which queries an allowlist of authoritative government health APIs (NIH MedlinePlus / ODS) with strict 5-second timeouts, 600-character truncation, citation metadata, and an offline fallback. It does **not** invoke Claude, OpenAI, or Gemini.

---

### 6. MongoDB Usage Reality
- **Question:** Is MongoDB used anywhere in user flows, or only as a health probe?
- **Empirical Resolution:** **Health probe only (OPTIONAL).**
  - All clinical knowledge tables are loaded directly into memory from curated CSV and YAML files (`knowledge/curated/`).
  - All user profiles, consent logs, careplan tasks, and saved summaries are persisted in relational storage (SQLite or MySQL).
  - In `backend/app/db/session.py`, MongoDB is probed safely; if missing, it reports `"status": "not configured (optional)"` without failing application health.

---

### 7. Reference Match % Calculation & ML Quarantining
- **Question:** Is `Reference match %` computed by deterministic formulas only? Which ML outputs feed user-facing results?
- **Empirical Resolution:**
  - `Reference match %` is **100% deterministic**, computed by `scoring_service.py` using IDF weighting, small-evidence shrinkage, and noisy-OR probability bounded at 95.0%.
  - **Decision C-30 Enforcement:** Machine learning models (XGBoost, LightGBM, and MobileNetV2) run in the quarantined **ML Lab** (`port 8001`) and never produce diagnostic claims.
  - **MedScan Blend (C-37):** In MedScan, vision model class predictions are weighted with shortcut penalties and blended with regional user checklists purely to propose informational reference tags for the deterministic matcher.

---

### 8. Exact Component and Metric Counts
- **API Endpoints:** Exactly **48 OpenAPI endpoints** (verified via `http://127.0.0.1:8000/openapi.json`).
- **Database Tables:** Exactly **5 relational tables** (`user_profiles`, `user_consent_logs`, `care_plan_items`, `saved_summaries`, `medscan_sessions`).
- **React Components:** Exactly **13 interactive view components** (15 `.tsx` files in `frontend/src/components/`, including modals and banners).
- **Safety-Scan Files:** Exactly **76 files** scanned by `backend/scripts/scan_safety_claims.py` (all passed with 0 violations).
- **End-to-End Smoke Steps:** Exactly **18 steps** in `scripts/smoke_e2e.py` (all 18 passed).
