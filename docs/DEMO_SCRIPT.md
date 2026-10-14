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
   - Results show exact matched tags (e.g., `2/3 reference tags matched`).
   - Displays clear review badges (`Unreviewed Draft Reference`).
   - Notice that **zero diagnostic probabilities, percentages, or certainty scores** are displayed.

### Act 3: Guided MedBot Wizard
1. Navigate to the **MedBot** tab.
2. Choose between **Simple Mode** (binary Yes/No questions) and **Standard Mode** (multiple choice).
3. Walk through the guided questions. Notice:
   - Every question can be safely skipped or answered.
   - Text-to-speech read-aloud button ("Listen") for accessibility.
   - Non-scoring lifestyle questions are clearly partitioned and **never alter reference-match results**.
4. Observe that MedBot produces **identical, deterministic reference results** to the Symptom Explorer.

### Act 4: Files & Reports
1. Navigate to **Reports**.
2. View the pre-seeded multi-region saved summaries (Nails, Eyes, Tongue).
3. Click any summary to view the complete reference-match snapshot and clinical review disclaimers.
4. Click **Print Report** to preview the clean, print-friendly CSS stylesheet that automatically hides navigation, buttons, and interactive controls for clinical consultations.
5. Inspect the **Monthly Check-in Timeline** aggregating historical assessments.

### Act 5: CarePlan Wellness Tasks
1. Navigate to **CarePlan**.
2. Review pre-seeded tasks: daily hydration, brisk walking, leafy greens nutrition, and sleep hygiene.
3. Attempt to add a prohibited task containing medication language (e.g. "Take vitamin pills" or "500mg dose"). Notice that the system strictly **rejects medication, drug, and supplement entries** (C-08, C-22).
4. Click **Export to Calendar (.ics)** to generate a standard RFC 5545 iCalendar file for Google Calendar or Apple Calendar.

### Act 6: MedScan-Lite (Image Quality Gate)
1. Navigate to **MedScan-Lite**.
2. Upload or capture an image.
3. Observe the client-side/server-side quality audit:
   - Discrete Laplacian variance blur check (rejects blurry photos).
   - Luminance and illumination boundary audit.
   - Strict 5 MB size gate and EXIF metadata stripping.
4. Confirm privacy guarantee: Raw image bytes are **ephemeral** and never persisted to cloud storage.

### Act 7: NurseBot (Scripted App Help)
1. Navigate to **NurseBot**.
2. Select a topic from the scripted FAQ menu (e.g., "How does Symptom Explorer work?").
3. Observe that NurseBot is **100% deterministic and scripted** (zero generative AI, zero LLM hallucinations, zero chat transcript storage).
4. Select the refusal topic: "Can NurseBot diagnose my condition?". Observe the strict medical refusal and clinician referral redirection.

### Act 8: Experimental ML Lab & Academic Honesty
1. Navigate to **ML Lab**.
2. **Tabular Models Tab**:
   - Inspect XGBoost and LightGBM models trained on the 4,000-row tabular dataset.
   - Explain the **Feature Leakage Gap**: The models achieve 99.4% accuracy when fed laboratory biomarkers, but accuracy drops to **79.9% (Macro-F1 0.633)** when restricted to user-reported symptoms, demonstrating why machine-learning models without laboratory data cannot reliably diagnose nutritional deficiency.
3. **Vision Models Tab**:
   - Inspect the 6 MobileNetV2 models trained on curated anatomical image datasets.
   - Highlight the **Shortcut Learning Badges**: MobileNetV2 models frequently achieve high benchmark accuracy by memorizing background illumination and clinical setting shortcuts rather than genuine pathology.
   - Demonstrate 100% Float32 TFLite parity on edge runtime.
   - Reiterate that ML models are strictly quarantined in this laboratory view and **never drive primary app logic**.

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
# 1. Full Backend Test Suite (67 tests, MySQL and SQLite):
cd backend
.\.venv\Scripts\pytest.exe -v

# 2. ML Stack Verification & TFLite Parity (40 tests):
cd ..
.\tf\.venv\Scripts\pytest.exe ml/tests/ -v

# 3. Automated End-to-End Smoke Test:
.\backend\.venv\Scripts\python.exe scripts/smoke_e2e.py

# 4. Prohibited Safety Claims Sweep:
.\backend\.venv\Scripts\python.exe backend/scripts/scan_safety_claims.py

# 5. Frontend Production Build:
cd frontend
npm run build
```
