# MedNourish — Educational Nutritional Health Prototype

> **CRITICAL MEDICAL DISCLAIMER (C-08, SAF-01, SAF-07)**
> MedNourish is an **academic engineering and educational prototype**. It is **NOT** a medical device, clinical decision support system, or autonomous diagnostic tool. It does **NOT** provide medical diagnoses, treatment plans, prescriptions, or dosages. All outputs represent informational reference mappings and experimental benchmark indicators. Never use this software for clinical triage or emergency care. In an emergency, dial local emergency services immediately (e.g. 112 / 911 / 999).

---

## 1. System Overview

MedNourish is an offline-capable, privacy-first educational health exploration platform designed to investigate transparent rule-based clinical lookup models and real machine-learning architectures for nutritional deficiency associations.

### Key Capabilities & Architectural Pillars
- **Symptom Reference Explorer**: Deterministic, transparent anatomical lookup against curated clinical knowledge bases (zero probabilities, zero risk scores).
- **MedBot (Questionnaire Bot)**: Guided assessment wizard in Simple and Standard modes with strict lifestyle/biomarker separation.
- **CarePlan Wellness Routines**: Self-directed lifestyle scheduling (hydration, nutrition, physical activity, sleep) with native `.ics` calendar export. **Zero medication or supplement reminders permitted.**
- **Files & Reports**: Local user timeline of saved reference matches with print-friendly CSS formatting for clinical consultations.
- **NurseBot Help**: 100% deterministic, scripted application FAQ and medical safety redirection system (zero generative AI, zero transcript persistence).
- **MedScan-Lite & Quality Gating**: Guided camera capture with client-side resolution and illumination quality audits.
- **VirtualWard Facility Directory**: Directory of local healthcare facilities with direct Google Maps navigation links and consultation voucher preparation.
- **Experimental ML Lab**: Isolated microservice (`ml/service/app.py` on port 8001) evaluating genuine Tabular models (XGBoost/LightGBM) and Computer Vision edge models (MobileNetV2 Float32 and quantized TFLite).

---

## 2. Repository Layout

```
MedNourish-Dev/
├── backend/                  # FastAPI backend server (Python 3.14/3.12)
│   ├── app/                  # Application core, routers, models, schemas
│   ├── scripts/              # Demo seeding (seed_demo.py) & safety sweep
│   └── tests/                # 57 comprehensive backend tests
├── frontend/                 # React 18 + Vite + TypeScript PWA
│   ├── src/components/       # UI Views: Dashboard, MedBot, CarePlan, MLLab, etc.
│   └── dist/                 # Production-optimized build assets
├── ml/                       # Machine Learning layer & benchmarks
│   ├── artifacts/            # Model cards, weights, TFLite models, Grad-CAMs
│   ├── class_maps/           # Per-region anatomical class mappings (YAML)
│   ├── manifests/            # Deduplicated train/val/test splits (JSONL)
│   ├── service/              # Port 8001 ML Lab microservice (FastAPI)
│   └── tests/                # 40 ML verification & parity gate tests
├── datasets/                 # Preserved raw data archives (Read-only)
├── docs/                     # Engineering specifications, logs, memory, audit
└── tf/                       # Dedicated Python 3.12 virtual environment for ML
```

---

## 3. Quickstart & One-Command Demo

MedNourish provides one-command startup and shutdown scripts for Windows that automatically clear target ports, launch background microservices with PID tracking, and verify reachability:

### One-Command Startup
```powershell
# In PowerShell:
powershell -ExecutionPolicy Bypass -File .\scripts\start_all.ps1

# Or in Windows Command Prompt:
.\scripts\start_all.cmd
```

**Services Started:**
- **Frontend UI:** [http://localhost:5173](http://localhost:5173)
- **Backend API:** [http://localhost:8000](http://localhost:8000)
- **OpenAPI Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check:** [http://localhost:8000/v1/health](http://localhost:8000/v1/health)
- **ML Lab Microservice:** [http://localhost:8001](http://localhost:8001)
- **Firebase Auth Emulator:** `http://127.0.0.1:9099`

### One-Command Shutdown
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\stop_all.ps1
# Or: .\scripts\stop_all.cmd
```

For a complete step-by-step 5-minute walkthrough of the prototype presentation, see [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md).

---

## 4. Database Modes (SQLite & MySQL)

MedNourish supports dual database modes via `DB_MODE` in `.env`:
- **SQLite (`DB_MODE=sqlite`)**: Zero-configuration local development. Uses `backend/mednourish_dev.db`.
- **MySQL (`DB_MODE=mysql`)**: Dedicated relational instance on `127.0.0.1:3306`. Targets `mednourish_dev` for application runtime and `mednourish_test` for isolated automated testing.

To seed the database with multi-region demo records (profile, consent, wellness tasks, saved summaries, MedScan session):
```powershell
cd backend
.\.venv\Scripts\python.exe scripts/seed_demo.py
```

---

## 5. Running Verification & Test Suites

MedNourish enforces 100% test pass gates across all application tiers:

1. **Backend Integration & Safety Suite** (98 passed, 1 skipped on both SQLite and MySQL):
   ```powershell
   cd backend
   .\.venv\Scripts\pytest.exe -v
   ```
2. **Machine Learning Pipeline & TFLite Parity Suite** (40 tests passing in Python 3.12 `tf/.venv`):
   ```powershell
   cd MedNourish-Dev
   $env:PYTHONPATH="."
   .\tf\.venv\Scripts\pytest.exe ml/tests/ -v
   ```
3. **Automated Real HTTP End-to-End Smoke Test** (17/17 tests passing, outputs `docs/SMOKE_RESULTS.md`):
   ```powershell
   cd MedNourish-Dev
   .\backend\.venv\Scripts\python.exe scripts/smoke_e2e.py
   ```
4. **Safety Claims & Prohibited Wording Scanner** (100% PASS across 72 files):
   ```powershell
   cd MedNourish-Dev
   .\backend\.venv\Scripts\python.exe backend/scripts/scan_safety_claims.py
   ```
5. **Frontend Production Build**:
   ```powershell
   cd frontend
   npm run build
   ```

---

## 5. Machine Learning Summary & Honest Academic Limitations

Detailed metrics, dataset inventories, and model cards are documented in:
- `docs/CSV_USE_MATRIX.md`: Complete audit of all 34 tabular datasets.
- `docs/DATASET_INVENTORY_v2.md`: Single source of truth inventory reconciling all 394,480 files across 8 directories.
- `docs/IMAGE_DATA_REPORT.md`: Perceptual hash deduplication, class gating, and train/val/test splits.
- `docs/ML_RESULTS.md`: Detailed performance metrics, baseline comparisons, Grad-CAM analysis, and TFLite parity gates.
- `docs/SCORING_SPEC.md` & `docs/ML_FEATURE_MAP.md`: Metric definitions, mathematical formulation, and multi-engine crosswalk.

### Critical Academic Limitations:
1. **Percentages Are Not Medical Probabilities**:
   - **Reference Match %**: Represents deterministic IDF-weighted coverage of unreviewed literature reference tables, not diagnostic likelihood or probability of disease.
   - **Model % (trained on unverified data)**: Derived from experimental synthetic multi-class tabular distributions; real-world clinical validity is zero.
   - **MedScan Blend %**: Heuristic fusion of regional visual feature classifiers with user checklist signs; does not estimate clinical severity or pathological presence.
2. **Image Models Are Dataset-Group Classifiers with Small Samples**:
   - MobileNetV2 vision models classify internet-scraped image subsets. Grad-CAM visual audits confirm models frequently leverage non-clinical shortcuts (background lighting, clinic walls, skin tone). Sample sizes for rare deficiency signs remain clinically insufficient.
3. **Web Answers Are Unreviewed General Knowledge**:
   - NurseBot's MedlinePlus/NIH web integration queries public educational documents with strict domain allowlists; responses are unreviewed machine extractions and must never substitute for individualized medical evaluation.
4. **Strict Educational Sandboxing**:
   - In compliance with `Rules.md`, all algorithms and models serve strictly pedagogical purposes. Prescriptions, diagnoses, and medical claims are technically and procedurally blocked.