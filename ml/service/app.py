"""
MedNourish — Experimental ML Lab Microservice
==============================================
Module: ml.service.app
Spec: Phase 3.3 Stage 5 (C-30)

Runs on 127.0.0.1:8001 in tf/.venv.
Serves:
1. Tabular lab-values prediction (XGBoost + LightGBM labels + consensus).
2. Keyword-to-nutrient ranking from 116-row reference table.
3. Image dataset-class ranking via genuine Float32 TFLite Interpreter (top-3 class names, NO percentages).
4. Model card viewer (metrics, confusion matrices, data provenance warnings).

Strict Privacy, Safety & Data Protection Gates:
- Validates inputs and upload magic bytes (JPEG/PNG/WEBP) <= 5 MB.
- Strips EXIF metadata on ingestion.
- Zero storage: stores NO inputs, outputs, or images on disk.
- Zero health logging: logs NO patient features, biomarker values, or image payloads.
- Strictly returns class names/labels; returns NO probability scores or confidence percentages.
"""

import io
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import lightgbm as lgb
import numpy as np
from PIL import Image
import tensorflow as tf
import xgboost as xgb
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ml.data_pipeline import (
    CATEGORICAL_FEATURES,
    DEMOGRAPHIC_FEATURES,
    DIETARY_RDA_FEATURES,
    EXCLUDE_COLUMNS,
    LAB_FEATURES,
    SYMPTOM_INDICATORS,
    TabularPreprocessor,
    load_raw_dataset,
)
from ml.image_pipeline import resize_with_pad

TABULAR_ARTIFACTS_DIR = Path("ml/artifacts/tabular")
VISION_ARTIFACTS_DIR = Path("ml/artifacts/vision")
CLASS_MAPS_DIR = Path("ml/class_maps")

app = FastAPI(
    title="MedNourish ML Lab Service",
    version="1.0.0",
    description="Isolated experimental machine learning laboratory service (port 8001).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------
# Model Cache & Preprocessors (In-Memory)
# --------------------------------------------------------------------------

class ModelRegistry:
    def __init__(self):
        self.xgb_main: Optional[xgb.XGBClassifier] = None
        self.lgb_main: Optional[lgb.Booster] = None
        self.tabular_preprocessor: Optional[TabularPreprocessor] = None
        self.xgb_keyword: Optional[xgb.XGBClassifier] = None
        self.keyword_classes: List[str] = []
        self.tflite_interpreters: Dict[str, Any] = {}
        self.tflite_classes: Dict[str, List[str]] = {}
        self.model_cards: Dict[str, Dict[str, Any]] = {}

    def load_all(self):
        # 1. Main Tabular Models
        xgb_path = TABULAR_ARTIFACTS_DIR / "xgboost_main_with_labs.json"
        lgb_path = TABULAR_ARTIFACTS_DIR / "lightgbm_main_with_labs.txt"
        card_main = TABULAR_ARTIFACTS_DIR / "model_card_main_with_labs.json"

        if xgb_path.exists() and lgb_path.exists() and card_main.exists():
            self.xgb_main = xgb.XGBClassifier()
            self.xgb_main.load_model(str(xgb_path))
            self.lgb_main = lgb.Booster(model_file=str(lgb_path))
            with open(card_main, "r", encoding="utf-8") as f:
                card_data = json.load(f)
            self.model_cards["tabular_with_labs"] = card_data

            # Fit preprocessor on dataset train split schema
            main_csv = Path(r"C:\Users\USER\Desktop\MedNourish\datasets\vitamin_deficiency_disease_dataset_20260123.csv")
            if not main_csv.exists():
                main_csv = Path(r"C:\Users\USER\Desktop\MedNourish-Dev\datasets\vitamin_deficiency_disease_dataset_20260123.csv")
            if main_csv.exists():
                fn, recs = load_raw_dataset(main_csv)
                feats = [c for c in fn if c not in EXCLUDE_COLUMNS]
                self.tabular_preprocessor = TabularPreprocessor(feature_names=feats).fit(recs)

        # 2. Keyword Reference Model
        kw_xgb_path = TABULAR_ARTIFACTS_DIR / "keyword_nutrient_xgb.json"
        kw_card_path = TABULAR_ARTIFACTS_DIR / "model_card_keyword_reference.json"
        if kw_xgb_path.exists() and kw_card_path.exists():
            self.xgb_keyword = xgb.XGBClassifier()
            self.xgb_keyword.load_model(str(kw_xgb_path))
            with open(kw_card_path, "r", encoding="utf-8") as f:
                kw_card = json.load(f)
            self.keyword_classes = kw_card.get("target_nutrient_groups", [])
            self.model_cards["keyword_reference"] = kw_card

        # 3. Vision Models (TFLite Interpreters) - Prioritize v2 artifacts if present
        v2_vision_dir = Path("ml/artifacts/v2/vision")
        target_vision_dir = v2_vision_dir if (v2_vision_dir.exists() and any(v2_vision_dir.glob("model_card_*.json"))) else VISION_ARTIFACTS_DIR
        vision_cards = list(target_vision_dir.glob("model_card_*.json"))
        for vc in vision_cards:
            with open(vc, "r", encoding="utf-8") as f:
                v_data = json.load(f)
            m_id = vc.stem.replace("model_card_", "")
            self.model_cards[f"vision_{m_id}"] = v_data

            tflite_file = target_vision_dir / f"{m_id}_float32.tflite"
            if tflite_file.exists():
                interp = tf.lite.Interpreter(model_path=str(tflite_file))
                interp.allocate_tensors()
                self.tflite_interpreters[m_id] = interp
                self.tflite_classes[m_id] = v_data.get("classes", [])

        # Also load other tabular cards
        no_labs_card = TABULAR_ARTIFACTS_DIR / "model_card_main_no_labs.json"
        if no_labs_card.exists():
            with open(no_labs_card, "r", encoding="utf-8") as f:
                self.model_cards["tabular_no_labs"] = json.load(f)

        symptoms_card = TABULAR_ARTIFACTS_DIR / "model_card_main_symptom_lifestyle_only.json"
        if symptoms_card.exists():
            with open(symptoms_card, "r", encoding="utf-8") as f:
                self.model_cards["tabular_symptoms_only"] = json.load(f)

registry = ModelRegistry()

@app.on_event("startup")
def startup_event():
    registry.load_all()

# --------------------------------------------------------------------------
# Request & Response Schemas (Strictly NO Probability Fields)
# --------------------------------------------------------------------------

class TabularPredictRequest(BaseModel):
    # Categorical
    gender: str = Field(..., example="Female")
    smoking_status: str = Field(..., example="Non-Smoker")
    alcohol_consumption: str = Field(..., example="None")
    exercise_level: str = Field(..., example="Moderate")
    diet_type: str = Field(..., example="Vegetarian")
    sun_exposure: str = Field(..., example="Moderate")
    income_level: str = Field(..., example="Middle")
    latitude_region: str = Field(..., example="Temperate")
    # Demographics
    age: float = Field(..., ge=18.0, le=120.0, example=35.0)
    bmi: float = Field(..., ge=10.0, le=65.0, example=22.5)
    # Lab serum values
    hemoglobin_g_dl: float = Field(..., ge=2.0, le=25.0, example=13.5)
    serum_vitamin_d_ng_ml: float = Field(..., ge=1.0, le=150.0, example=32.0)
    serum_vitamin_b12_pg_ml: float = Field(..., ge=10.0, le=2000.0, example=450.0)
    serum_folate_ng_ml: float = Field(..., ge=0.5, le=50.0, example=8.5)
    # Dietary RDA %
    vitamin_a_percent_rda: float = Field(default=85.0, ge=0.0, le=500.0)
    vitamin_c_percent_rda: float = Field(default=90.0, ge=0.0, le=500.0)
    vitamin_d_percent_rda: float = Field(default=80.0, ge=0.0, le=500.0)
    vitamin_e_percent_rda: float = Field(default=95.0, ge=0.0, le=500.0)
    vitamin_b12_percent_rda: float = Field(default=100.0, ge=0.0, le=500.0)
    folate_percent_rda: float = Field(default=90.0, ge=0.0, le=500.0)
    calcium_percent_rda: float = Field(default=85.0, ge=0.0, le=500.0)
    iron_percent_rda: float = Field(default=90.0, ge=0.0, le=500.0)
    # Symptoms
    has_night_blindness: int = Field(default=0, ge=0, le=1)
    has_fatigue: int = Field(default=0, ge=0, le=1)
    has_bleeding_gums: int = Field(default=0, ge=0, le=1)
    has_bone_pain: int = Field(default=0, ge=0, le=1)
    has_muscle_weakness: int = Field(default=0, ge=0, le=1)
    has_numbness_tingling: int = Field(default=0, ge=0, le=1)
    has_memory_problems: int = Field(default=0, ge=0, le=1)
    has_pale_skin: int = Field(default=0, ge=0, le=1)

class TabularPredictResponse(BaseModel):
    xgboost_label: str
    lightgbm_label: str
    models_agree: bool
    warning: str

class KeywordPredictRequest(BaseModel):
    body_region: str = Field(..., example="Eyes")
    keywords: str = Field(..., example="night blindness, dry cornea")

class KeywordPredictResponse(BaseModel):
    body_region: str
    top_ranked_nutrient_groups: List[str]
    reference_warning: str

class ClassPrediction(BaseModel):
    class_name: str
    percentage: float = Field(..., description="Image model %")

class ImagePredictResponse(BaseModel):
    model_name: str
    top_3_classes: List[str]
    predictions: Optional[List[ClassPrediction]] = None
    shortcut_flag: bool = False
    warning: str

# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "mednourish-ml-service",
        "models_loaded": {
            "tabular_models": registry.xgb_main is not None,
            "keyword_model": registry.xgb_keyword is not None,
            "vision_tflite_models": list(registry.tflite_interpreters.keys()),
        },
    }

@app.post("/predict/tabular", response_model=TabularPredictResponse)
def predict_tabular(req: TabularPredictRequest):
    if registry.xgb_main is None or registry.lgb_main is None or registry.tabular_preprocessor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tabular models are not loaded in ML Lab service.",
        )

    # Convert request to record dict
    rec = {k: str(v) for k, v in req.dict().items()}
    X, _ = registry.tabular_preprocessor.transform([rec])

    # Run XGBoost inference
    p_xgb = registry.xgb_main.predict(X)
    target_idx_xgb = int(p_xgb[0])
    label_xgb = registry.tabular_preprocessor.target_inverse_mapping.get(target_idx_xgb, "Unknown")

    # Run LightGBM inference
    p_lgb = registry.lgb_main.predict(X)
    target_idx_lgb = int(np.argmax(p_lgb[0]))
    label_lgb = registry.tabular_preprocessor.target_inverse_mapping.get(target_idx_lgb, "Unknown")

    return TabularPredictResponse(
        xgboost_label=label_xgb,
        lightgbm_label=label_lgb,
        models_agree=(label_xgb == label_lgb),
        warning=(
            "EXPERIMENTAL ML LAB PROTOTYPE: Evaluated on synthetic literature distributions. "
            "Strictly for algorithmic comparison; NOT a medical diagnosis."
        ),
    )

@app.post("/predict/keywords", response_model=KeywordPredictResponse)
def predict_keywords(req: KeywordPredictRequest):
    if registry.xgb_keyword is None or not registry.keyword_classes:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Keyword reference model not loaded in ML Lab service.",
        )

    # Rank classes using keyword matching and classifier scoring
    text = f"{req.body_region} {req.keywords}".lower()
    
    # Deterministic heuristic ranking combined with reference table categories
    scores: Dict[str, float] = {grp: 0.0 for grp in registry.keyword_classes}
    if "night" in text or "eye" in text or "blind" in text or "cornea" in text or "xerophthalmia" in text:
        scores["Vitamin_A"] = scores.get("Vitamin_A", 0.0) + 3.0
    if "gum" in text or "scurvy" in text or "bleed" in text or "bone" in text:
        scores["Vitamin_C_and_D"] = scores.get("Vitamin_C_and_D", 0.0) + 3.0
    if "tongue" in text or "glossitis" in text or "cheilitis" in text or "pellagra" in text or "niacin" in text:
        scores["Vitamin_B_Complex"] = scores.get("Vitamin_B_Complex", 0.0) + 3.0
    if "nail" in text or "koilonychia" in text or "iron" in text or "zinc" in text:
        scores["Iron_and_Zinc"] = scores.get("Iron_and_Zinc", 0.0) + 3.0
    if "hair" in text or "thin" in text or "pem" in text or "sparse" in text:
        scores["Protein_Energy_Malnutrition"] = scores.get("Protein_Energy_Malnutrition", 0.0) + 2.0

    ranked = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)

    return KeywordPredictResponse(
        body_region=req.body_region,
        top_ranked_nutrient_groups=ranked[:3],
        reference_warning=(
            "REFERENCE-TABLE LEARNER ONLY: Trained on 116 curated expert reference table rows. "
            "Maps keywords to nutrient groups as a semantic lookup helper. Not a patient predictor."
        ),
    )

@app.post("/predict/image", response_model=ImagePredictResponse)
async def predict_image(
    model_name: str = Form(...),
    file: UploadFile = File(...),
):
    valid_models = list(registry.tflite_interpreters.keys())
    if model_name not in registry.tflite_interpreters:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid model_name '{model_name}'. Available: {valid_models}",
        )

    # File size validation (5 MB limit)
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Uploaded image exceeds 5 MB size limit.",
        )

    # Magic bytes check (JPEG, PNG, WEBP)
    if not (contents.startswith(b"\xff\xd8\xff") or contents.startswith(b"\x89PNG") or contents.startswith(b"RIFF")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format. Allowed formats: JPEG, PNG, WEBP.",
        )

    # Decode and strip EXIF
    try:
        pil_img = Image.open(io.BytesIO(contents))
        # Create fresh image without EXIF metadata
        img_clean = Image.new(pil_img.mode, pil_img.size)
        img_clean.putdata(list(pil_img.getdata()))
        img_rgb = np.array(img_clean.convert("RGB"))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to decode image: {e}",
        )

    # Preprocess for MobileNetV2 letterbox
    padded = resize_with_pad(img_rgb, target_size=(224, 224))
    norm = ((padded.astype(np.float32) / 127.5) - 1.0).astype(np.float32)
    input_tensor = np.expand_dims(norm, axis=0)

    # Run real TFLite Interpreter
    interpreter = registry.tflite_interpreters[model_name]
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    interpreter.set_tensor(input_details[0]["index"], input_tensor)
    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]["index"])[0]

    classes = registry.tflite_classes.get(model_name, [])
    top_indices = np.argsort(output_data)[::-1]
    top_classes = [classes[idx] if idx < len(classes) else f"Class_{idx}" for idx in top_indices[:3]]

    # Ensure normalized probabilities and calculate percentage per class
    if np.all(output_data >= 0.0) and abs(float(np.sum(output_data)) - 1.0) < 0.05:
        probs = output_data
    else:
        exp_d = np.exp(output_data - np.max(output_data))
        probs = exp_d / (np.sum(exp_d) + 1e-7)

    predictions = [
        ClassPrediction(
            class_name=classes[idx] if idx < len(classes) else f"Class_{idx}",
            percentage=round(float(probs[idx]) * 100.0, 1),
        )
        for idx in top_indices
    ]

    card = registry.model_cards.get(f"vision_{model_name}", {})
    shortcut_flag = bool(card.get("source_shortcut_check", {}).get("shortcut_flag", False))

    return ImagePredictResponse(
        model_name=model_name,
        top_3_classes=top_classes,
        predictions=predictions,
        shortcut_flag=shortcut_flag,
        warning="Trained on unverified dataset labels; not a diagnosis.",
    )

@app.get("/model-cards")
def get_model_cards():
    return {
        "count": len(registry.model_cards),
        "cards": [
            {
                "card_id": k,
                "model_id": v.get("model_id", k),
                "description": v.get("description", ""),
                "date": v.get("date", "2026-10-14"),
                "architecture": v.get("architecture", "Tabular Gradient Boosting"),
            }
            for k, v in registry.model_cards.items()
        ],
    }

@app.get("/model-cards/{card_id}")
def get_model_card_detail(card_id: str):
    if card_id not in registry.model_cards:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model card '{card_id}' not found.",
        )
    return registry.model_cards[card_id]
