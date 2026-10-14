# MedNourish — Academic Demonstration Walkthrough & Script

> **MANDATORY EDUCATIONAL PROTOTYPE NOTICE (SAF-01, SAF-07, C-08)**  
> MedNourish is an **academic engineering demonstration prototype**. It is **NOT** a clinical decision support system, diagnostic tool, or medical device. It does not provide medical diagnoses, treatment recommendations, prescriptions, or drug/supplement dosages. All outputs represent transparent informational reference mappings and experimental academic machine-learning benchmarks.

---

## 1. Quick Launch

MedNourish features a one-command launch script that brings up all microservices with automatic port clearing and PID tracking:

```powershell
# From the repository root (PowerShell):
powershell -ExecutionPolicy Bypass -File .\scripts\start_all.ps1

# Or from Windows Command Prompt:
.\scripts\start_all.cmd
```

**Services Started:**
- **Frontend UI:** [http://localhost:5173](http://localhost:5173)
- **Backend API:** [http://localhost:8000](http://localhost:8000)
- **Interactive OpenAPI Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check Endpoint:** [http://localhost:8000/v1/health](http://localhost:8000/v1/health)
- **ML Lab Microservice:** [http://localhost:8001](http://localhost:8001)
- **Firebase Auth Emulator:** `http://127.0.0.1:9099`

---

## 2. 5-Minute Demonstration Walkthrough

### Act 1: Safety Shell & Privacy-Preserving Onboarding
1. **Open [http://localhost:5173](http://localhost:5173)** in any browser.
2. Observe the persistent, non-dismissible **Yellow Educational Prototype Banner** across the top of every screen.
3. Observe the persistent **Red "Emergency Help" Button** in the navigation header, immediately accessible whether signed in or signed out. Click it to reveal immediate crisis numbers (112, 911, 999).
4. Sign in with fictional demo credentials (or click "Login with Demo Account").
5. Review the **Adult Consent Gate**: Mandatory confirmation that the user is 18+ and agrees to prototype terms v1.0. Note that MedNourish **never collects or stores date of birth or age** (PROF-01).

### Act 2: Symptom Reference Explorer
1. Navigate to the **Explorer** tab.
2. Select anatomical region **Nails** or **Eyes**.
3. Select symptom tags (e.g. `brittlenails`, `spoon_shaped_nails`).
4. Click **Run Reference Match**.
5. Observe the transparent, deterministic set-intersection matching against curated clinical lookup tables:
   - Results show exact matched tags and reference match percentage bars with demo risk bands (C-34, C-35).
   - Expandable "Why" panels explaining matched vs missing symptoms.
   - Displays clear review badges (`Unreviewed Draft Reference`).

### Act 3: Guided MedBot Wizard & Text Extraction
1. Navigate to the **MedBot** tab.
2. Choose between **Simple Mode** (binary Yes/No questions) and **Standard Mode** (multiple choice).
3. Try free-text symptom description input; observe automated symptom chip extraction using synonyms dictionary.
4. Walk through the guided questions:
   - Every question can be safely skipped or answered.
   - Text-to-speech read-aloud button ("Listen") for accessibility.
   - Non-scoring lifestyle questions are clearly partitioned and never alter reference-match results.
5. Click Evaluate to view reference match percentages and auto-save summaries.

### Act 4: Files, Reports & Recency-Weighted Aggregation
1. Navigate to **Reports**.
2. View pre-seeded and newly generated saved summaries across body regions.
3. Review the **6 Responsive Visualizations** (Nutrient Overview Radar, Regional Breakdown, Recency-Weighted Trend, Risk Matrix, Correlation Heatmap, Assessment History).
4. Inspect the **Final Report Card** summarizing cross-region findings.
5. Click **Print Report** to preview print-friendly CSS stylesheet.

### Act 5: CarePlan Wellness Tasks & Auto-Sync
1. Navigate to **CarePlan**.
2. Review active routines (water, food, exercise, sleep hygiene).
3. Observe automated CarePlan task sync from MedBot and MedScan assessments:
   - Safely strips supplemental terms (e.g. "vitamin pill", "tablets") and timeframe phrases (e.g. "for 2 weeks").
   - Filters out all pharmaceutical/dosage language.
4. Click **Export to Calendar (.ics)** to generate a standard RFC 5545 iCalendar file.

### Act 6: MedScan (Multimodal Vision & Quality Gate)
1. Navigate to **MedScan**.
2. Upload or capture an image.
3. Observe the client-side/server-side quality audit (Laplacian variance blur check >= 50, luminance boundary audit, 5 MB limit, EXIF stripping).
4. Select matching anatomical checklist symptoms.
5. Run analysis: microservice executes v2 multitask MobileNetV2 with shortcut-penalty weighting blended with reference checklist.
6. Observe resulting match bars and automatic saved summary creation.

### Act 7: NurseBot (WhatsApp Chat & Verified NIH Search)
1. Navigate to **NurseBot**.
2. Interact via WhatsApp-style chat bubbles with quick suggestion chips and typing indicators.
3. Test app guidance questions (e.g., "How do I use MedScan?").
4. Ask a general health/nutrition question: observe WebAnswerService fetching real-time educational snippets strictly from NIH/MedlinePlus with citation links, 600-char truncation, and disclaimer.
5. Test emergency keywords (e.g., "chest pain", "can't breathe"): observe immediate emergency routing modal.

### Act 8: Experimental ML Lab & Academic Honesty
1. Navigate to **ML Lab**.
2. **Tabular Models Tab**:
   - Inspect XGBoost and LightGBM models trained on the 4,000-row tabular dataset.
   - Explain the Feature Leakage Gap: models achieve >99% with lab biomarkers, but drop to 79.9% (Macro-F1 0.633) on symptoms alone.
   - Test live profile inference via `/predict/tabular_profile`.
3. **Vision Models Tab**:
   - Inspect 7-region v2 MobileNetV2 models with support gate >= 40 images.
   - Review 100% Float32 TFLite parity (max diff < 1.5e-5).
   - Reiterate that ML models are strictly quarantined benchmarks and never drive primary clinical diagnosis.

---

## 3. Clean Teardown

To stop all background services cleanly and free ports 9099, 8001, 8000, and 5173:

```powershell
# From the repository root (PowerShell):
powershell -ExecutionPolicy Bypass -File .\scripts\stop_all.ps1

# Or from Windows Command Prompt:
.\scripts\stop_all.cmd
```

---

## 4. Verification & QA Commands

```powershell
# 1. Full Backend Test Suite (98 passed, 1 skipped, MySQL and SQLite):
cd backend
.\.venv\Scripts\pytest.exe -v

# 2. ML Stack Verification & TFLite Parity (40 tests):
cd ..
.\tf\.venv\Scripts\pytest.exe ml/tests/ -v

# 3. Automated End-to-End Real HTTP Smoke Test (17/17 PASS):
.\backend\.venv\Scripts\python.exe scripts/smoke_e2e.py

# 4. Prohibited Safety Claims Sweep (100% PASS across 72 files):
.\backend\.venv\Scripts\python.exe backend/scripts/scan_safety_claims.py

# 5. Frontend Production Build:
cd frontend
npm run build
```
