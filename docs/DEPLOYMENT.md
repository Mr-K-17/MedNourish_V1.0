# MedNourish Deployment & Distribution Guide

## 1. What Is Published
- **Application Source:** Complete FastAPI backend and React 19 / TypeScript frontend.
- **Reference Schemas:** Curated anatomical mapping CSVs (`knowledge/curated/`), `synonyms.yaml`, `food_items.csv`, `nutrient_guidance.csv`.
- **Static Landing Page:** `site/index.html` showcasing architecture, benchmarks, and limitations.
- **CI/CD Configurations:** GitHub Actions (`.github/workflows/ci.yml`, `pages.yml`) and GitLab CI (`.gitlab-ci.yml`).

## 2. What Is NOT Published
- **Raw Datasets:** 370k+ images and 4,000-row tabular CSVs excluded.
- **Model Weight Binaries:** `*.keras`, `*.tflite`, `*.onnx`, `*.pt`, `*.h5` excluded.
- **Environment & DB Files:** `.env*`, `*.db`, `*.sqlite*`, caches, and build artifacts excluded.
- **Historical Git History:** Monolithic development history excluded; published with clean snapshot history.

## 3. How to Enable GitHub Pages
1. Navigate to the GitHub repository: `https://github.com/Mr-K-17/MedNourish_V1.0`.
2. Open **Settings** > **Pages** (under "Code and automation").
3. Under **Build and deployment** > **Source**, select **GitHub Actions**.
4. The deployment workflow triggers automatically on push to `main` and publishes to `https://mr-k-17.github.io/MedNourish_V1.0/`.

## 4. Running the Full Stack Locally (SQLite Mode)
```bash
# Backend
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && export DB_MODE=sqlite
python -m uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npm ci && npm run dev
```

## 5. Dataset Access
Datasets are withheld due to licensing, provenance verification, and patient privacy boundaries. For research inquiries regarding evaluation protocols, contact repository maintainers.
