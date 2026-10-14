# MedNourish — End-to-End Automated Smoke Test Results (F5)

**Execution Date:** 2026-10-14 05:03:04 UTC  
**Execution Mode:** In-Process ASGI Transport  
**Database Engine:** MYSQL  
**Summary:** 14/14 tests PASSED (0 failed)  

---

## Verified Endpoints & Flow Status

| Feature / Test | Target Endpoint | HTTP Status | Result | Details |
|:---|:---|:---:|:---:|:---|
| **Root Disclaimer** | `GET /` | 200 | **PASS** | Project: MEDNOURISH, Disclaimer present |
| **System Health** | `GET /v1/health` | 200 | **PASS** | DB: unknown |
| **Explorer Categories** | `GET /v1/explorer/categories` | 200 | **PASS** | Regions count: 6 |
| **Explorer Match** | `POST /v1/explorer/match` | 200 | **PASS** | Matches: 1 conditions, deterministic set-intersection |
| **MedBot Questions** | `GET /v1/medbot/questions` | 200 | **PASS** | Available questions: 8 |
| **MedBot Evaluation** | `POST /v1/medbot/evaluate` | 200 | **PASS** | Matches returned: 7 |
| **NurseBot Menu** | `GET /v1/nursebot/menu` | 200 | **PASS** | Menu topics available: 9 (scripted only) |
| **NurseBot Safety Refusal** | `GET /v1/nursebot/topics/refusal_diagnosis` | 200 | **PASS** | Scripted refusal topic verified: Can NurseBot diagnose my condition or illness? |
| **ML Lab Gateway** | `GET /v1/mllab/status` | 503 | **PASS** | ML microservice offline (503 handled gracefully) |
| **Saved Summaries** | `GET /v1/reports/summaries` | 200 | **PASS** | Saved demo summaries retrieved: 3 across regions |
| **Reports Timeline** | `GET /v1/reports/timeline` | 200 | **PASS** | Timeline check-in history points: 1 |
| **CarePlan Wellness Tasks** | `GET /v1/careplan/tasks` | 200 | **PASS** | Active wellness tasks: 4 (zero medications) |
| **MedScan-Lite Quality Check** | `POST /v1/medscan/sessions` | 201 | **PASS** | Image count: 1, Resolution OK: True |
| **Prohibited Claims Sweep** | `Audit All Payloads` | 200 | **PASS** | Prohibited terms found: [] (must be empty) |

---

## Educational Prototype Safety Guarantees

1. **Zero Diagnostic Claims:** No endpoint returns affirmative diagnoses or certainty scores.
2. **Zero Medication Language:** CarePlan and Suggested Routine endpoints reject prescription drugs and dosage regimens.
3. **Ephemeral Image Ingestion:** MedScan-lite executes in-memory quality checks without disk persistence.
4. **Deterministic Matcher Parity:** MedBot and Symptom Explorer produce identical reference-table intersections.
