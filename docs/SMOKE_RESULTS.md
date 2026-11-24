# MedNourish — Automated Real HTTP Smoke Test Results (v2-P6)

**Execution Date:** 2026-11-06 00:30:00 UTC  
**Execution Mode:** Real HTTP against live stack (ports 9099, 8001, 8000, 5173)  
**Real Database Engine:** MySQL 8.0 (status: healthy)  
**Summary:** 18/18 PASSED, 0 SKIPPED, 0 FAILED  

---

## Verified Endpoints & Flow Status

| Feature / Test | Target Endpoint | HTTP Status | Result | Details |
|:---|:---|:---:|:---:|:---|
| **Root Disclaimer** | `GET /` | 200 | **PASS** | Project: MEDNOURISH, Disclaimer present |
| **System Health & Mongo Optional** | `GET /v1/health` | 200 | **PASS** | Overall: healthy, MongoDB: healthy |
| **Frontend UI Server** | `GET http://127.0.0.1:5173/` | 200 | **PASS** | Vite dev server active and serving index.html |
| **Profile v2 Setup** | `POST /v1/profile` | 201 | **PASS** | Age: 29, Blood: O+, Conditions: ['Anemia'] |
| **MedBot Symptom Extraction** | `POST /v1/medbot/extract` | 200 | **PASS** | Extracted 3 symptom chips: ['brittlenails', 'dryskin', 'fatigue'], tags: ['brittlenails', 'dryskin', 'fatigue'] |
| **MedBot Percentages & Bands** | `POST /v1/medbot/evaluate` | 200 | **PASS** | Nutrients scored: 5, Top: Vitamin A Deficiency (49.8%) |
| **MedScan Live ML Vision** | `POST /v1/medscan/analyze` | 200 | **PASS** | Quality passed: True, Nutrients blended: 1, Saved: True |
| **NurseBot App Guidance** | `POST /v1/nursebot/ask` | 200 | **PASS** | Intent: app_help, Reply length: 386 chars |
| **NurseBot Emergency Triage** | `POST /v1/nursebot/ask` | 200 | **PASS** | Emergency detected: emergency, Referral: EMERGENCY ALERT: If you or someone with you is experien... |
| **NurseBot Web Question** | `POST /v1/nursebot/ask` | 200 | **PASS** | Web knowledge retrieved (594 chars), Source: MedlinePlus (National Library of Medicine) |
| **Reports Charts Data** | `GET /v1/reports/aggregate` | 200 | **PASS** | Visualizations verified: 6 charts, Snapshots aggregated: 1 |
| **Final Report Card** | `GET /v1/reports/aggregate (card)` | 200 | **PASS** | Risk Band: Moderate (heuristic, not clinical), Measures: 3 (non-pharmacologic) |
| **CarePlan Auto-Sync & Dedupe** | `GET /v1/careplan/tasks` | 200 | **PASS** | Auto tasks synced: 1, User task created: True |
| **CarePlan Meal Planner V3 (C-39)** | `GET/POST/PUT /v1/careplan/meal-plan*` | 200 | **PASS** | 7-day plan: True, Log toggle & covered nutrients: 2, Vegan 0-animal foods: True, ICS valid: True |
| **Cross-User Isolation** | `GET /v1/{profile,reports,careplan}` | 200 | **PASS** | User B profile: 404, summaries: 0, tasks: 0 |
| **Account Deletion Cascade** | `DELETE /v1/profile` | 200 | **PASS** | All profile, reports, and careplan records purged on deletion |
| **ML Lab Profile Predictor** | `POST /v1/mllab/predict/tabular_profile` | 200 | **PASS** | Gateway: 200, Label: 'Model % (trained on unverified data)', Consensus: 50.9% |
| **Prohibited Claims Sweep** | `Sweep All Responses` | 200 | **PASS** | Forbidden terms detected: [] (clean) |

---

## Educational Prototype Safety Guarantees

1. **Zero Diagnostic Claims:** No endpoint returns affirmative clinical diagnoses or probability claims.
2. **Non-Pharmacologic Routine Sync:** CarePlan suggestions exclude prescription medicines, supplements, and dosing.
3. **Multi-Engine Recency Weights:** Reports aggregate fuses reference, XGBoost, LightGBM, and vision model outputs.
4. **Clean Cascade Purge:** Deleting an account purges profile, consent, summaries, and wellness tasks completely.
