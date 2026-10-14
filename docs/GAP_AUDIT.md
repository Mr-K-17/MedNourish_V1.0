# MedNourish — Gap Audit Matrix (F1)

**Audit Date:** 2026-10-14  
**Audit Method:** Codebase inspection by grep / direct file examination.

| Feature Area | Status | Evidence / File Path | Gap Summary & Action Plan |
|:---|:---:|:---|:---|
| **1. Auth + Emulator Login** | **Done** | `backend/app/core/auth.py`, `frontend/src/services/firebase.ts`, `frontend/src/components/AuthForm.tsx` | Authenticates against local Firebase Auth emulator (port 9099). Rejects unauthenticated tokens (401). |
| **2. 18+ Adult Consent Gate** | **Done** | `frontend/src/components/ConsentProfileModal.tsx`, `backend/app/api/v1/profile.py` | Explicit adult checkbox + terms consent v1.0 required before dashboard access. |
| **3. Minimal Demographic Profile** | **Done** | `backend/app/models/user.py`, `backend/app/schemas/profile.py` | Gender, height, weight optional. Zero DOB or age stored (PROF-01). |
| **4. Account Deletion Cascade** | **Done** | `backend/app/api/v1/profile.py:delete_user_account` | Deletes profile, consent logs, careplan items, and saved summaries upon account deletion. (Will add MedScan sessions cascade in F2). |
| **5. Emergency Help on Every Screen** | **Done** | `frontend/src/App.tsx`, `frontend/src/components/EmergencyHelpModal.tsx` | Persistent red button reachable when signed in, signed out, and in all views (C-20). |
| **6. Prototype Banner on Every Screen** | **Done** | `frontend/src/components/DemoBanner.tsx`, `frontend/src/App.tsx` | Fixed educational banner rendered at the top of the application shell. |
| **7. Symptom Explorer** | **Done** | `backend/app/api/v1/explorer.py`, `frontend/src/components/SymptomExplorer.tsx` | Curated reference table set-intersection matching (zero probabilities/bands). |
| **8. MedBot (Simple + Standard)** | **Done** | `backend/app/api/v1/medbot.py`, `frontend/src/components/MedBotView.tsx` | Simple & Standard modes, question skipping, optional non-scoring lifestyle questions, Explorer parity. |
| **9. NurseBot** | **Done** | `backend/app/api/v1/nursebot.py`, `frontend/src/components/NurseBotView.tsx` | 100% deterministic scripted FAQs and safety refusal patterns. Zero LLMs, zero transcript storage. |
| **10. Saved Summaries** | **Done** | `backend/app/api/v1/reports.py`, `frontend/src/components/ReportsView.tsx` | Snapshot reference-table saving, ownership isolation, detail inspection. |
| **11. CarePlan CRUD** | **Done** | `backend/app/api/v1/careplan.py`, `frontend/src/components/CarePlanView.tsx` | Create, list, complete, delete wellness routines (water, food, exercise, sleep). Zero medication. |
| **12. CarePlan .ics Export** | **Done** | `frontend/src/components/CarePlanView.tsx:handleExportICS` | Exports standard RFC 5545 iCalendar schedule for Google Calendar / Apple Calendar. |
| **13. 'Add Suggested Routine' on Saved Summary** | **Partial** | Curated CSVs in `knowledge/curated/*_routine_clean.csv` exist. | Needs backend endpoint `POST /v1/reports/summaries/{id}/suggested-routines` and frontend button in `ReportsView.tsx`. |
| **14. VirtualWard 'Create Check-up Reminder'** | **Partial** | `frontend/src/components/VirtualWardView.tsx` | Needs cleanup of placeholder hospital names to generic search terms, and wiring of 'Create check-up reminder' button directly to CarePlan. |
| **15. Reports Timeline** | **Partial** | `backend/app/api/v1/reports.py`, `frontend/src/components/ReportsView.tsx` | Needs `GET /v1/reports/timeline` endpoint (monthly count per body area) and UI timeline overview card. |
| **16. Print CSS** | **Done** | `frontend/src/components/ReportsView.module.css:@media print` | Clean print-friendly stylesheet hiding navigation and interactive buttons. |
| **17. MedScan-Lite** | **Partial** | `frontend/src/components/MedScanLiteView.tsx` | Frontend quality audit exists; needs backend router `/v1/medscan/sessions` (save, list, delete, cascade, 5MB limit, Pillow Laplacian blur check). |
| **18. VirtualWard** | **Partial** | `frontend/src/components/VirtualWardView.tsx` | Replace hard-coded fictitious phone/names with generic facility categories ("Local General Hospital", "Community Health Center") and direct Google Maps query. |
| **19. ML Lab** | **Done** | `backend/app/api/v1/mllab.py`, `ml/service/app.py`, `frontend/src/components/MLLabView.tsx` | Isolated port 8001 microservice, backend proxy, 4 tabs (Tabular, Keywords, Vision Classes, Model Cards), labels only. |
| **20. Seed Demo Data** | **Done** | `backend/scripts/seed_demo.py` | Idempotent SQLite seeding of adult profile, consent log, 4 wellness routines, and saved summary. |
| **21. DB_MODE Switch** | **Partial** | `backend/app/core/config.py`, `backend/app/db/session.py` | Default uses MySQL credentials or SQLite fallback; needs explicit `DB_MODE` toggle (`sqlite` vs `mysql`). |
