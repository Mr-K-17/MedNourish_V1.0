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

## 3. Quickstart & Local Demo Runbook

### Prerequisites
- Node.js 18+ and npm
- Python 3.12+ (or 3.14 for backend, 3.12 for ML)
- Local Firebase Emulator Suite (Authentication emulator on port 9099)
- Local SQLite (default) or MySQL 8.0 instance

---

### Step 1: Backend Setup & Demo Seeding
```powershell
cd backend
# Create / activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# Populate reproducible fictional demo data (1 profile, 4 wellness tasks, 1 summary)
python scripts\seed_demo.py

# Launch FastAPI backend on port 8000
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

### Step 2: Frontend Setup & Launch
```powershell
cd frontend
npm install
npm run build   # Verifies TypeScript types & generates production bundle
npm run dev     # Starts local development server on http://localhost:5173
```

---

### Step 3: Experimental ML Lab Microservice (Optional)
To test genuine XGBoost/LightGBM tabular consensus and MobileNetV2 edge models in the ML Lab tab:
```powershell
# Using the dedicated Python 3.12 ML environment:
cd MedNourish-Dev
.\tf\.venv\Scripts\python.exe ml\service\app.py
# Runs on http://127.0.0.1:8001
```

---

## 4. Running Test Suites

MedNourish enforces 100% test pass gates across all application tiers:

1. **Backend Integration & Safety Suite** (57 tests):
   ```powershell
   cd backend
   .\.venv\Scripts\pytest.exe tests/ -v
   ```
2. **Machine Learning Pipeline & TFLite Parity Suite** (40 tests):
   ```powershell
   cd MedNourish-Dev
   $env:PYTHONPATH="."
   .\tf\.venv\Scripts\pytest.exe ml/tests/ -v
   ```
3. **Frontend Production Build**:
   ```powershell
   cd frontend
   npm run build
   ```
4. **Safety Claims & Prohibited Wording Scanner**:
   ```powershell
   cd backend
   .\.venv\Scripts\python.exe scripts/scan_safety_claims.py
   ```

---

## 5. Machine Learning Summary & Honest Academic Limitations

Detailed metrics, dataset inventories, and model cards are documented in:
- `docs/CSV_USE_MATRIX.md`: Complete audit of all 34 tabular datasets.
- `docs/DATASET_INVENTORY_v2.md`: Single source of truth inventory reconciling all 394,480 files (364,292 images, 8,244 masks, 21,936 annotations) across 8 directories.
- `docs/IMAGE_DATA_REPORT.md`: Perceptual hash deduplication, class gating (>=100 samples), and train/val/test splits.
- `docs/ML_RESULTS.md`: Detailed performance metrics, baseline comparisons, Grad-CAM analysis, and TFLite parity gates.

### Summary of Honest Findings:
1. **The Tabular Leakage Gap**: On the 4k-row synthetic dataset, models achieve 99.4% accuracy when fed laboratory biomarkers. However, when restricted to symptoms and lifestyle features (the actual user-facing app task), accuracy drops to **79.9% (Macro-F1 0.633)**, demonstrating significant feature dependency and real-world clinical invalidity.
2. **Vision Shortcut Learning**: Grad-CAM overlays reveal that MobileNetV2 models trained on internet-scraped clinical photos frequently focus on **background lighting, hospital wall artifacts, and surgical draping** rather than actual biological pathology.
3. **Strict Model Gating**: In compliance with `Rules.md`, models are confined to the **Experimental ML Lab** sandbox and are never used to drive user-facing triage or symptom explorer results.