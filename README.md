# MedNourish — Educational Nutritional Health Prototype

> **CRITICAL MEDICAL DISCLAIMER (C-08, SAF-01, SAF-07)**
> MedNourish is an **academic engineering and educational prototype**. It is **NOT** a medical device, clinical decision support system, or autonomous diagnostic tool. It does **NOT** provide medical diagnoses, treatment plans, prescriptions, or dosages. All outputs represent informational reference mappings and experimental benchmark indicators. Never use this software for clinical triage or emergency care. In an emergency, dial local emergency services immediately (e.g. 112 / 911 / 999).

> **ONLINE DEMO & GITHUB PAGES:**
> A static landing and demonstration overview is available at: **[https://mr-k-17.github.io/MedNourish_V1.0/](https://mr-k-17.github.io/MedNourish_V1.0/)**

> **DATASET & MODEL WEIGHTS NOTICE:**
> In accordance with project governance rules, **raw training datasets (~31 GB, 394,000+ files) and compiled model binary weights (`*.keras`, `*.tflite`) are NOT included** in this public repository. Third-party data provenance and redistribution licences remain unverified. Model cards, architecture scripts, training pipelines, and curated clinical mappings are fully provided.

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
MedNourish/
├── backend/                  # FastAPI backend server (Python 3.14/3.12)
│   ├── app/                  # Application core, routers, models, schemas
│   ├── scripts/              # Demo seeding (seed_demo.py) & safety sweep
│   └── tests/                # Comprehensive backend tests
├── frontend/                 # React 18 + Vite + TypeScript PWA
│   ├── src/components/       # UI Views: Dashboard, MedBot, CarePlan, MLLab, etc.
│   └── dist/                 # Production build assets
├── ml/                       # Machine Learning layer & benchmarks
│   ├── artifacts/            # Model cards, evaluation summaries, Grad-CAMs
│   ├── class_maps/           # Per-region anatomical class mappings (YAML)
│   ├── manifests/            # Deduplicated split specifications
│   ├── service/              # Port 8001 ML Lab microservice (FastAPI)
│   └── tests/                # ML verification & parity gate tests
├── knowledge/                # Curated everyday food catalog & mapping tables
├── docs/                     # Engineering specifications, memory, and audit reports
└── site/                     # Static GitHub Pages web assets
```

---

## 3. Quickstart: Running Locally

### Prerequisites
- Node.js 18+ and npm
- Python 3.12 or 3.14
- (Optional) Local Firebase CLI for auth emulation (`npm install -g firebase-tools`)

### Local Setup & Run Steps

1. **Install Frontend Dependencies & Run**:
   ```powershell
   cd frontend
   npm install
   npm run dev
   ```
   Open `http://localhost:5173`.

2. **Install Backend & Run (Local SQLite Mode)**:
   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   uvicorn app.main:app --port 8000 --host 127.0.0.1
   ```
   API Swagger docs available at `http://localhost:8000/docs`.

3. **Run ML Microservice (Optional)**:
   ```powershell
   cd ml/service
   python -m uvicorn app:app --port 8001 --host 127.0.0.1
   ```

4. **One-Command Startup (Windows)**:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\start_all.ps1
   ```
   To stop: `powershell -ExecutionPolicy Bypass -File .\scripts\stop_all.ps1`.

---

## 4. Running Verification & Test Suites

MedNourish enforces test pass gates across all application tiers:

1. **Backend Integration & Safety Suite**:
   ```powershell
   cd backend
   pytest -v
   ```
2. **Safety Claims & Prohibited Wording Scanner**:
   ```powershell
   python backend/scripts/scan_safety_claims.py
   ```
3. **Frontend Production Build**:
   ```powershell
   cd frontend
   npm run build
   ```

---

## 5. Machine Learning Summary & Honest Academic Limitations

Detailed metrics, dataset inventories, and model cards are documented in:
- `docs/CSV_USE_MATRIX.md`: Complete audit of tabular datasets.
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
