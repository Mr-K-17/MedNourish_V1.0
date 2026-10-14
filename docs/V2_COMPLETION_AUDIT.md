# MedNourish v2 — Completion Audit Matrix (Step C Final)

**Audit Date:** 2026-10-14  
**Audit Branch:** `dev`  
**Rollback Base:** `final-demo` (`cc51f6e`)  
**Status Before Fixes:** 21 Done, 4 Partial, 0 Missing  
**Final Status:** 25 Done, 0 Partial, 0 Missing (100% Complete)

---

## Final Verification
- **Backend Test Suite (SQLite):** 98 passed, 1 skipped in 84.68s (`pytest backend/tests`).
- **Backend Test Suite (MySQL `mednourish_test`):** 98 passed, 1 skipped in 85.97s (`pytest backend/tests`).
- **ML Test Suite:** 40 passed in 31.25s (`pytest ml/tests`).
- **Safety Claims Scanner:** 100% PASS across 72 audited files (`scan_safety_claims.py`).
- **Frontend Production Build:** 2,405 modules cleanly transformed in 4.78s (`npm run build`).
- **Smoke Test Suite:** 17/17 passed against live stack (`scripts/smoke_e2e.py`).
- **8 End-to-End Live HTTP Journeys:** 8/8 passed (`scripts/test_8_journeys.py`).

---

## Checklist Audit Table

| # | Item Description | Status | Evidence & Verification Proof |
|:---:|:---|:---:|:---|
| **1** | Profile model age (1-120), blood_type (9 values), conditions (JSON list), other_condition (<=100 chars); schemas & endpoints | **Done** | `backend/app/models/user.py`, `backend/app/schemas/profile.py`, verified with `pytest backend/tests/test_profile.py -k test_v2_profile_extensions_c33` (PASSED). |
| **2** | Idempotent migration on SQLite and MySQL (run twice on `mednourish_test`) | **Done** | `backend/scripts/migrate_v2_profile.py` ran twice consecutively on SQLite, `mednourish_dev`, and `mednourish_test`, logging zero duplicate columns and exit code 0. |
| **3** | 18+ gate replaced by demo-consent checkbox; under-18 notice shown: "Reference content is written for adults; demo only." | **Done** | `frontend/src/components/ConsentProfileModal.tsx:201` renders exact notice upon age < 18; demo consent checkbox at line 150 replaces strict adult gate. |
| **4** | UI: age field, blood type select, 18-condition multi-select chips + 'None'/'Other', accessible & validated; profile edit screen | **Done** | `ConsentProfileModal.tsx` provides full validated inputs for age, blood type, conditions, and other condition; `App.tsx` wires accessible "Edit Profile" button opening modal in edit mode (committed in `a1b814d`). |
| **5** | Account deletion cascade covers new fields; `seed_demo` updated; `scan_safety_claims` allowlist updated | **Done** | `UserProfile` cascade delete verified in `test_profile.py:test_profile_update_and_account_deletion`; `seed_demo.py` seeds age/blood_type/conditions; `scan_safety_claims.py` allowlist updated and passes 100%. |
| **6** | Amendments C-33..C-38 recorded in Memory.md/PRD/Rules | **Done** | Documented in `docs/Rules.md:207-220`, `docs/PRD.md:129,181`, and `docs/Memory.md:S-043..S-048`. |
| **7** | `docs/SCORING_SPEC.md` and `scoring_service.py` (IDF-weighted row %, shrinkage, cap 95, noisy-OR group %, band thresholds) | **Done** | `backend/app/services/scoring_service.py` implements all mathematical specifications with config threshold injection; verified in `backend/tests/test_scoring.py`. |
| **8** | Scoring tests: determinism x10, monotonicity, bounds 0-100, every curated row retrievable | **Done** | `backend/tests/test_scoring.py` (6/6 tests PASSED: determinism, monotonicity, bounds, shrinkage, all 116 rows retrievable). |
| **9** | Explorer and MedBot results show percent bars labelled 'Reference match %' with one-line explanation; expandable 'why'; old summaries render | **Done** | `frontend/src/components/SymptomExplorer.tsx:458-472` and `frontend/src/components/MedBotView.tsx:550-565` render bars with `percentage_kind` and `percentage_explanation`; `ReportsView.tsx` backward-compatible. |
| **10** | `knowledge/curated/synonyms.yaml` exists, loads, has >= 150 phrasings | **Done** | `app.services.extraction_service.load_synonyms_from_yaml` loads 257 unique symptom phrasings from `knowledge/curated/synonyms.yaml` without external dependencies. |
| **11** | `POST /v1/medbot/extract`: synonym + fuzzy (>=0.88) + negation; raw text never stored; auth required; tests; MedBot Standard free-text chips | **Done** | `backend/tests/test_extraction.py` (5/5 tests PASSED); `frontend/src/components/MedBotView.tsx:730-800` renders free-text input with add/remove chips and retains all questions. |
| **12** | v2 vision models (eyes, hair, lips, nails, skin, tongue, combined) trained with min 40 images/class, model cards, TFLite float32 parity, `ML_RESULTS.md`, ml-service loads v2 | **Done** | `ml/artifacts/v2/vision/` contains 7 models + TFLite Float32 + model cards; `docs/ML_RESULTS.md` documents metrics (all 100% TFLite parity); `ml/service/app.py:150` prioritizes v2 directory. |
| **13** | `ml/class_maps/image_to_nutrient.yaml` exists and is used | **Done** | `backend/app/services/medscan_service.py` loads `image_to_nutrient.yaml` directly via `_parse_yaml_mappings` with JSON fallback (committed in `b011aa3`). |
| **14** | MedScan pipeline: quality check -> body area -> ml-service prediction (%) -> nutrient mapping -> checklist -> blend (weights/caps/shortcuts); fallback; auto-saved; no tensorflow import | **Done** | `backend/tests/test_medscan.py` (13/13 tests PASSED); zero tensorflow imports in `backend/app/` (verified clean via Select-String); fallback verified in Journey 8. |
| **15** | WhatsApp-style chat UI (bubbles, timestamps, typing indicator, quick-reply chips, text field); original predefined questions still work | **Done** | `frontend/src/components/NurseBotView.tsx` implements responsive bubbles, typing state, chip buttons, and predefined FAQ items. |
| **16** | `POST /v1/nursebot/ask` with 5-way router (emergency first, app Q&A, web, refusal, out of scope); rate limit 10/min; no transcripts | **Done** | `backend/tests/test_nursebot.py` (14/14 tests PASSED: emergency routing, app help, refusal, rate limiting, and zero transcript logging); verified in live Journey 4. |
| **17** | `web_answer_service.py`: allowlist (NIH/MedlinePlus), 5s timeout, max 2 requests, HTML stripped, <= 600 char excerpt, cache, offline fallback; live call confirmed | **Done** | Live call confirmed returning 549 chars from MedlinePlus (National Library of Medicine); verified in live Journey 4 and Smoke Test. |
| **18** | ml-service `predict/tabular_profile` + backend proxy; `docs/ML_FEATURE_MAP.md`; 'estimated' flags; label 'Model % (trained on unverified data)' | **Done** | `ml/service/app.py:328`, `backend/app/api/v1/mllab.py:121`, `docs/ML_FEATURE_MAP.md`, verified with `test_reports_aggregate.py:test_mllab_predict_tabular_profile_proxy` (PASSED). |
| **19** | Every entry (MedBot, Explorer, MedScan) stores reference %, XGBoost %, LightGBM %, image % in snapshot; aggregate latest 5; auto-save with notice | **Done** | `backend/app/api/v1/medbot.py`, `medscan.py`, and `reports.py` populate `snapshot_scores_json` via `scoring_service.evaluate_tags` and auto-save (committed in `db53f6e`); verified in Journey 2 & 5. |
| **20** | ReportsView charts (recharts pinned): grouped bar, ranked bar, radar, donut, line, heatmap; percentage kind captions; print CSS; chart-data endpoint | **Done** | `recharts` pinned to 2.12.7; all 6 charts rendered in `ReportsView.tsx:360-520`; print media stylesheet verified; tested via `test_reports_aggregate.py`. |
| **21** | Final report card: screening summary, demo risk band, supporting sources, suggested measures, disclaimer, Emergency Help link; clean wording | **Done** | `ReportsView.tsx:296-345` renders composite card with zero banned diagnostic/supplement language; Emergency Help button wired; verified in Journey 5. |
| **22** | CarePlan auto-sync: top 2 nutrients >= 30%, dietary/lifestyle/follow-up only, drug terms stripped, auto flag + source_entry_id, dedupe, stale below 30, user items preserved, High band clinician item; triggered after EVERY new entry | **Done** | CarePlan sync service verified in `test_reports_aggregate.py`; triggered on MedScan, Reports, and MedBot saves (committed in `db53f6e`); verified in live Journey 2 (3 tasks created). |
| **23** | MongoDB health label: 'not configured (optional)' / 'unavailable' without failing overall health; frontend label fixed; old error cause documented | **Done** | `backend/app/db/session.py:check_mongodb_health`, `backend/tests/test_health.py` (4/4 tests PASSED); frontend banner updated in `App.tsx:195`. |
| **24** | `scripts/smoke_e2e.py` uses REAL HTTP against live stack, prints real DB engine, covers all v2 features, 503 is FAIL, offline is SKIPPED | **Done** | 17/17 PASS against live stack (ports 9099, 8001, 8000, 5173), real MySQL DB engine verified, output written to `docs/SMOKE_RESULTS.md`. |
| **25** | `scan_safety_claims` clean (72 files); suites green on SQLite + MySQL; frontend build clean; docs updated with 'Limitations'; tag `v2-demo` | **Done** | Safety scanner 100% PASS; SQLite & MySQL test suites 98 passed, 1 skipped; docs updated; local tag `v2-demo` created. |
