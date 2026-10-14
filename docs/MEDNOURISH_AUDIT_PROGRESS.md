# MedNourish Audit & Phase Progress Matrix

**Project:** MedNourish-Dev (branch `dev`)  
**Base Rollback Point:** `final-demo` (`cc51f6e`)  
**Target Release Tag:** `v2-demo`  
**Prototype Classification:** Educational Engineering Demonstration Prototype (SAF-01, SAF-07, C-08)  

---

## 1. Owner Amendments & Core Decisions (C-33 through C-38)

| Decision ID | Core Directive | Implementation Path & Verification | Status |
| :--- | :--- | :--- | :---: |
| **C-33** | Additive Evolution (Retain Existing Baseline) | Existing 67 backend & 40 ML tests preserved. All APIs remain backward compatible. | **Enforced** |
| **C-34** | Transparent Scoring Spec (Reference Match %) | Deterministic set-intersection $\frac{\|S_{\text{user}} \cap S_{\text{ref}}\|}{\|S_{\text{ref}}\|} \times 100$. Explicitly NOT clinical probability. | **Enforced** |
| **C-35** | Educational Prototype Risk Bands | Low (<34%), Moderate (34-66%), High (>=67%) reference match bands with clear academic disclaimers. | **Enforced** |
| **C-36** | Multitask Vision Models (Support Gate >= 40) | 7 anatomical regions, >= 40 support gate, 100% Float32 TFLite parity, shortcut penalty. | **Enforced** |
| **C-37** | NurseBot External Search Grounding | Strictly allowlisted domains (`nih.gov`, `medlineplus.gov`), 5s timeout, 24h cache, 600-char truncation. | **Enforced** |
| **C-38** | Recency-Weighted Reports & CarePlan Sync | Exponential decay half-life 30d, 6 Recharts charts, auto-sync stripping supplements/timeframes. | **Enforced** |

---

## 2. Phase Execution & Milestone Log

### Phase 1: Planning, Architectural Reconciliation & Owner Alignment
- **Milestone:** Align architecture and rules with C-33..C-38 amendments; establish rollback point at `final-demo`.
- **Status:** Complete.

### Phase 2: Scoring Spec, Reference Match %, & MedBot Extraction
- **Milestone:** Implement deterministic reference match scoring, why panels, risk bands, and symptom extraction from text.
- **Artifacts:** `docs/SCORING_SPEC.md`, `backend/app/services/scoring_service.py`, `backend/app/services/extraction_service.py`, `backend/app/data/synonyms.yaml`.
- **Tests:** 11/11 Phase 2 tests passed; 78 backend tests passed.
- **Commit:** `v2-P2: Scoring spec, reference match %, why breakdown, and MedBot symptom extraction` (`4ad1767`).
- **Status:** Complete.

### Phase 3: Multitask Vision v2 Models & Blend Pipeline
- **Milestone:** Train 7-region v2 MobileNetV2 models (support >= 40), generate TFLite Float32 models, build blend pipeline.
- **Artifacts:** `ml/train/train_v2_vision.py`, `ml/artifacts/v2/vision/`, `backend/app/services/vision_service.py`, `frontend/src/components/MedScanLiteView.tsx`.
- **Tests:** 13 MedScan tests passed; 100% TFLite top-1 parity across 754 test images.
- **Commit:** `v2-P3: Multitask vision v2 models, crosswalk, and MedScan blend pipeline` (`b539fa9`).
- **Status:** Complete.

### Phase 4: NurseBot WhatsApp UI & Verified Web Search
- **Milestone:** Build WhatsApp-style chat interface, intent router (emergency, guidance, search), and NIH/MedlinePlus fetcher.
- **Artifacts:** `backend/app/services/web_answer_service.py`, `backend/app/api/v1/nursebot.py`, `frontend/src/components/NurseBotView.tsx`.
- **Tests:** 14 NurseBot tests passed; 90 backend tests passed.
- **Commit:** `v2-P4: NurseBot WhatsApp UI, intent router, and verified NIH/MedlinePlus search` (`322b647`).
- **Status:** Complete.

### Phase 5: Tabular Predictor, Recency-Weighted Aggregation, & CarePlan Sync
- **Milestone:** Add `/predict/tabular_profile`, multi-engine aggregate service with exponential decay, 6 Recharts visualizations, and CarePlan auto-sync.
- **Artifacts:** `backend/app/services/reports_aggregate_service.py`, `backend/app/services/careplan_sync_service.py`, `backend/app/api/v1/reports.py`, `frontend/src/components/ReportsView.tsx`.
- **Tests:** 96 backend tests passed; 40 ML tests passed; 72 files safety scan passed.
- **Commit:** `v2-P5: Tabular profile predictor, recency-weighted reports, and CarePlan sync` (`5f22e99`).
- **Status:** Complete.

### Phase 6: MongoDB Optional Health Probe, Real HTTP Smoke Test, & Release
- **Milestone:** Probe MongoDB optionally ("not configured (optional)" / "unavailable"), 17/17 automated real HTTP smoke test suite, full documentation update.
- **Artifacts:** `backend/app/db/session.py`, `backend/app/core/config.py`, `backend/tests/test_health.py`, `scripts/smoke_e2e.py`, `docs/SMOKE_RESULTS.md`, `README.md`, `docs/DEMO_SCRIPT.md`, `docs/FINAL_VERIFICATION.md`, `docs/GAP_AUDIT.md`.
- **Tests:** 98 backend tests passed (1 skipped) on SQLite & MySQL; 40 ML tests passed; 17/17 real HTTP smoke tests passed; safety claims scan 100% passed across 72 files; frontend Vite production build passed cleanly.
- **Status:** Complete.
