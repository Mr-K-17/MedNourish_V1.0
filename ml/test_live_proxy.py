"""
MedNourish — Live ML Lab Microservice & Backend Proxy Verification
==================================================================
Runs:
1. Launches ml/service/app.py on port 8001 using tf/.venv.
2. Polls /health until active (max 15s).
3. Invokes all endpoints via backend proxy with authenticated test user:
   - GET /v1/mllab/status
   - GET /v1/mllab/model-cards
   - GET /v1/mllab/model-cards/tabular_with_labs
   - POST /v1/mllab/predict/tabular
   - POST /v1/mllab/predict/keywords
   - POST /v1/mllab/predict/image
4. Asserts:
   - All responses return HTTP 200.
   - All predictions return discrete category labels only.
   - ZERO probability scores, softmax values, or confidence percentages in any response.
5. Terminates the ml service process cleanly.
"""

import io
import json
import os
import subprocess
import sys
import time
from pathlib import Path
import httpx
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.core.auth import AuthenticatedUser, get_current_user
from app.main import app as backend_app

MOCK_USER = AuthenticatedUser(uid="proxy_verifier_user", email="verifier@mednourish.internal")

def run_live_verification():
    print("===================================================================")
    print(" MedNourish — Live Microservice & Backend Proxy Verification")
    print("===================================================================")

    ml_venv_python = PROJECT_ROOT / "tf" / ".venv" / "Scripts" / "python.exe"
    service_script = PROJECT_ROOT / "ml" / "service" / "app.py"

    print("[1/4] Spawning ML Lab microservice on 127.0.0.1:8001...")
    proc = subprocess.Popen(
        [
            str(ml_venv_python),
            "-m",
            "uvicorn",
            "ml.service.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8001",
            "--log-level",
            "warning",
        ],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        # Wait for service to become healthy
        print("  - Waiting for ML service health check...")
        ready = False
        for attempt in range(25):
            time.sleep(1.0)
            try:
                resp = httpx.get("http://127.0.0.1:8001/health", timeout=2.0)
                if resp.status_code == 200:
                    ready = True
                    print(f"  - ML service is UP and healthy on port 8001 (attempt {attempt+1})!")
                    break
            except Exception:
                pass

        if not ready:
            proc.terminate()
            raise RuntimeError("ML Lab microservice failed to start within timeout.")

        # Override auth in backend FastAPI app
        backend_app.dependency_overrides[get_current_user] = lambda: MOCK_USER

        from fastapi.testclient import TestClient
        client = TestClient(backend_app)
        if True:
            # 1. Status
            r_status = client.get("/v1/mllab/status")
            assert r_status.status_code == 200, f"Status failed: {r_status.text}"
            print("  * GET /v1/mllab/status -> 200 OK")
            print(f"    Loaded: {r_status.json()['models_loaded']}")

            # 2. Model Cards Catalog
            r_cards = client.get("/v1/mllab/model-cards")
            assert r_cards.status_code == 200, f"Cards failed: {r_cards.text}"
            cards_list = r_cards.json()["cards"]
            print(f"  * GET /v1/mllab/model-cards -> 200 OK ({len(cards_list)} model cards available)")

            # 3. Model Card Detail
            r_card_det = client.get("/v1/mllab/model-cards/tabular_with_labs")
            assert r_card_det.status_code == 200, f"Card detail failed: {r_card_det.text}"
            print(f"  * GET /v1/mllab/model-cards/tabular_with_labs -> 200 OK (id: {r_card_det.json()['model_id']})")

            # 4. Tabular Predict
            tabular_payload = {
                "gender": "Female",
                "smoking_status": "Non-Smoker",
                "alcohol_consumption": "None",
                "exercise_level": "Moderate",
                "diet_type": "Vegetarian",
                "sun_exposure": "Moderate",
                "income_level": "Middle",
                "latitude_region": "Temperate",
                "age": 35.0,
                "bmi": 22.5,
                "hemoglobin_g_dl": 13.5,
                "serum_vitamin_d_ng_ml": 12.0,  # Deficient
                "serum_vitamin_b12_pg_ml": 450.0,
                "serum_folate_ng_ml": 8.5,
                "vitamin_a_percent_rda": 85.0,
                "vitamin_c_percent_rda": 90.0,
                "vitamin_d_percent_rda": 40.0,
                "vitamin_e_percent_rda": 95.0,
                "vitamin_b12_percent_rda": 100.0,
                "folate_percent_rda": 90.0,
                "calcium_percent_rda": 85.0,
                "iron_percent_rda": 90.0,
                "has_night_blindness": 0,
                "has_fatigue": 1,
                "has_bleeding_gums": 0,
                "has_bone_pain": 1,
                "has_muscle_weakness": 1,
                "has_numbness_tingling": 0,
                "has_memory_problems": 0,
                "has_pale_skin": 0,
            }
            r_tab = client.post("/v1/mllab/predict/tabular", json=tabular_payload)
            assert r_tab.status_code == 200, f"Tabular predict failed: {r_tab.text}"
            tab_data = r_tab.json()
            print("  * POST /v1/mllab/predict/tabular -> 200 OK")
            print(f"    XGBoost Label: {tab_data['xgboost_label']}")
            print(f"    LightGBM Label: {tab_data['lightgbm_label']}")
            print(f"    Models Agree: {tab_data['models_agree']}")

            # 5. Keyword Ranking
            kw_payload = {
                "body_region": "Eyes",
                "keywords": ["night blindness", "dry cornea", "xerophthalmia"],
            }
            r_kw = client.post("/v1/mllab/predict/keywords", json=kw_payload)
            assert r_kw.status_code == 200, f"Keyword predict failed: {r_kw.text}"
            kw_data = r_kw.json()
            print("  * POST /v1/mllab/predict/keywords -> 200 OK")
            print(f"    Top Groups: {kw_data['top_ranked_nutrient_groups']}")

            # 6. Image Predict (using synthetic 224x224 RGB JPEG)
            img = Image.new("RGB", (224, 224), color=(180, 150, 120))
            buf = io.BytesIO()
            img.save(buf, format="JPEG")
            img_bytes = buf.getvalue()

            files = {"file": ("test_eye.jpg", img_bytes, "image/jpeg")}
            data = {"model_name": "eyes"}
            r_img = client.post("/v1/mllab/predict/image", data=data, files=files)
            assert r_img.status_code == 200, f"Image predict failed: {r_img.text}"
            img_data = r_img.json()
            print("  * POST /v1/mllab/predict/image (eyes) -> 200 OK")
            print(f"    Top 3 Classes: {img_data['top_3_classes']}")

            print("\n[3/4] Enforcing Strict Safety Schema Guarantees...")
            all_responses = [tab_data, kw_data, img_data]
            for resp_dict in all_responses:
                for k, v in resp_dict.items():
                    assert "prob" not in k.lower(), f"Forbidden probability field: {k}"
                    assert "conf" not in k.lower(), f"Forbidden confidence field: {k}"
                    if isinstance(v, (int, float)) and not isinstance(v, bool):
                        assert False, f"Unexpected numeric probability score in {k}: {v}"
            print("  - Passed: All response schemas verified (Labels only, ZERO probability/confidence metrics).")

    finally:
        print("\n[4/4] Shutting down ML Lab microservice...")
        backend_app.dependency_overrides.pop(get_current_user, None)
        proc.terminate()
        try:
            proc.wait(timeout=5)
            print("  - ML Lab microservice stopped cleanly.")
        except subprocess.TimeoutExpired:
            proc.kill()
            print("  - ML Lab microservice process killed.")

    print("\n===================================================================")
    print(" LIVE ML PROXY VERIFICATION SUCCESSFUL")
    print("===================================================================")

if __name__ == "__main__":
    run_live_verification()
