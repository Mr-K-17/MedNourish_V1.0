"""
MedNourish — Backend MedScan Blend Service (Phase 3.c)
=====================================================
Module: app.services.medscan_service
Spec: Phase 3 (c)

Architectural Guarantees:
- Backend NEVER imports TensorFlow or OpenCV.
- Communicates with ml-service on http://127.0.0.1:8001 via httpx.
- Quality check -> Model selection -> Image prediction (Image model %)
  -> Nutrient crosswalk -> Region follow-up checklist -> Blended inference.
- Blend formula:
  nutrient % = image_evidence * w_img + reference_match * (1 - w_img)
  where w_img = 0.5 normally, 0.25 if shortcut flag detected.
  Image-only results capped at 60.0% and labelled 'image only, low reliability'.
- Kind: 'medscan_blend' (image part labelled 'Image model %').
- Graceful fallback: If ml-service is down, evaluates symptoms only.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import httpx

from app.services.knowledge_service import knowledge_repo, normalize_tag
from app.services.scoring_service import (
    KIND_REFERENCE_MATCH,
    RISK_BAND_LABEL,
    calculate_risk_band,
    scoring_service,
)

logger = logging.getLogger(__name__)

ML_SERVICE_URL = "http://127.0.0.1:8001"
TIMEOUT_SECONDS = 15.0

# Discriminative regional checklist tags (6-8 items per region)
REGION_CHECKLIST: Dict[str, List[Dict[str, str]]] = {
    "eyes": [
        {"tag": "eyedryness", "label": "Eye dryness / Bitot's spots"},
        {"tag": "nightblindness", "label": "Difficulty seeing in dim light / night blindness"},
        {"tag": "cornealsoftening", "label": "Corneal softening / ulceration"},
        {"tag": "blurredvision", "label": "Blurred or fluctuating vision"},
        {"tag": "eyegrittiness", "label": "Gritty sensation in eyes"},
        {"tag": "photophobia", "label": "Sensitivity to light"},
        {"tag": "excessivetearing", "label": "Excessive tearing or burning"},
    ],
    "nails": [
        {"tag": "koilonychia", "label": "Spoon-shaped concave nails (koilonychia)"},
        {"tag": "brittlenails", "label": "Brittle, splitting or peeling nails"},
        {"tag": "beaulines", "label": "Transverse nail ridges (Beau's lines)"},
        {"tag": "longitudinalridges", "label": "Vertical / longitudinal nail ridging"},
        {"tag": "palenails", "label": "Pale nail beds (pallor)"},
        {"tag": "slowgrowth", "label": "Slow nail growth or frequent breakage"},
    ],
    "hair": [
        {"tag": "brittlehair", "label": "Dry, brittle or easily broken hair"},
        {"tag": "diffusehairloss", "label": "Diffuse hair thinning or shedding"},
        {"tag": "corkscrewhair", "label": "Corkscrew or coiled hairs"},
        {"tag": "curlyhairshaft", "label": "Fragile curly hair shafts"},
        {"tag": "lossheadhair", "label": "Patches of hair thinning / alopecia"},
        {"tag": "depigmentation", "label": "Lightening or depigmentation of hair"},
    ],
    "lips": [
        {"tag": "crackedlips", "label": "Dry, peeling or cracked lips (cheilosis)"},
        {"tag": "angularcheilitis", "label": "Fissures / sores at corners of mouth"},
        {"tag": "burningtongue", "label": "Burning sensation on lips or mouth"},
        {"tag": "swollenlips", "label": "Swollen or erythematous lips"},
        {"tag": "lipfissures", "label": "Deep painful fissures on lips"},
    ],
    "skin": [
        {"tag": "follicularhyperkeratosis", "label": "Rough, gooseflesh-like skin bumps"},
        {"tag": "dryskin", "label": "Severe dry, scaly or flaking skin (xerosis)"},
        {"tag": "darkenedskinpatches", "label": "Dark, hyperpigmented skin patches"},
        {"tag": "petechiae", "label": "Small pinpoint red/purple spots (petechiae)"},
        {"tag": "delayedwoundhealing", "label": "Slow wound healing or easy bruising"},
        {"tag": "burningskin", "label": "Burning or prickling sensations on skin"},
    ],
    "tongue": [
        {"tag": "beefyredtongue", "label": "Smooth, beefy red tongue (atrophic glossitis)"},
        {"tag": "burningtongue", "label": "Burning or tender sensation on tongue"},
        {"tag": "swollentongue", "label": "Swollen or enlarged tongue"},
        {"tag": "papillaryatrophy", "label": "Loss of tongue bumps / papillae"},
        {"tag": "tastealteration", "label": "Altered or blunted taste perception"},
        {"tag": "tongueulcers", "label": "Recurrent aphthous-like sores on tongue"},
    ],
    "combined": [
        {"tag": "nightblindness", "label": "Night blindness / dark adaptation difficulty"},
        {"tag": "fatigue", "label": "Persistent exhaustion or weakness"},
        {"tag": "bleedinggums", "label": "Spontaneous bleeding gums"},
        {"tag": "brittlenails", "label": "Brittle, fragile nails"},
        {"tag": "crackedlips", "label": "Cracked lip corners (angular cheilitis)"},
        {"tag": "bonepain", "label": "Deep bone or joint aching"},
        {"tag": "delayedwoundhealing", "label": "Delayed healing of cuts or scrapes"},
    ],
}


DEFAULT_IMAGE_TO_NUTRIENT: Dict[str, Dict[str, Optional[str]]] = {
    "combined": {
        "Vitamin_A_Deficiency": "Vitamin A Deficiency",
        "Vitamin_B_Complex_Deficiency": "Vitamin B Complex Deficiency",
        "Vitamin_B12_Deficiency": "Vitamin B12 Deficiency",
        "Vitamin_B2_Deficiency": "Vitamin B2 Deficiency",
        "Vitamin_B3_Deficiency": "Vitamin B3 Deficiency",
        "Vitamin_B9_Deficiency": "Vitamin B9 Deficiency",
        "Vitamin_C_Deficiency": "Vitamin C Deficiency",
        "Vitamin_D_Deficiency": "Vitamin D Deficiency",
        "Vitamin_E_Deficiency": "Vitamin E Deficiency",
        "Vitamin_K_Deficiency": "Vitamin K Deficiency",
        "Other_Nutrient_Deficiency": "Iron Deficiency",
    },
    "eyes": {
        "Vitamin_A_Deficiency": "Vitamin A Deficiency",
        "Normal": None,
        "Other_Non_Nutritional": None,
    },
    "hair": {
        "Normal": None,
        "Other_Non_Nutritional": None,
    },
    "lips": {
        "NUTRITIONAL": "Vitamin B Complex Deficiency",
        "Normal": None,
        "NON_NUTRITIONAL": None,
    },
    "nails": {
        "Nutritional": "Iron Deficiency",
        "NORMAL": None,
        "Other_Non_Nutritional": None,
    },
    "skin": {
        "Vitamin_B3_Pellagra": "Vitamin B3 Deficiency",
        "VITAMIN_A": "Vitamin A Deficiency",
        "VITAMIN_C": "Vitamin C Deficiency",
        "ZINC": "Zinc Deficiency",
        "BIOTIN": "Biotin B7 Deficiency",
        "Normal": None,
        "Other_Non_Nutritional": None,
    },
    "tongue": {
        "Healthy": None,
        "Diabetes": None,
        "OralCancer": None,
        "Other_TCM_Tongue": None,
    },
}


def normalize_nutrient_key(name: str) -> str:
    n = name.strip()
    nl = n.lower()
    if nl in ["vitamin a", "vitamin a deficiency"]:
        return "Vitamin A Deficiency"
    if nl in ["vitamin b complex", "vitamin b complex deficiency"]:
        return "Vitamin B Complex Deficiency"
    if nl in ["vitamin b12", "vitamin b12 deficiency"]:
        return "Vitamin B12 Deficiency"
    if nl in ["vitamin b2", "vitamin b2 deficiency"]:
        return "Vitamin B2 Deficiency"
    if nl in ["vitamin b3", "vitamin b3 deficiency", "niacin"]:
        return "Vitamin B3 Deficiency"
    if nl in ["vitamin b6", "vitamin b6 deficiency"]:
        return "Vitamin B6 Deficiency"
    if nl in ["vitamin b9", "vitamin b9 deficiency", "folate", "folic acid"]:
        return "Vitamin B9 Deficiency"
    if nl in ["vitamin c", "vitamin c deficiency"]:
        return "Vitamin C Deficiency"
    if nl in ["vitamin d", "vitamin d deficiency"]:
        return "Vitamin D Deficiency"
    if nl in ["vitamin e", "vitamin e deficiency"]:
        return "Vitamin E Deficiency"
    if nl in ["vitamin k", "vitamin k deficiency"]:
        return "Vitamin K Deficiency"
    if nl in ["iron", "iron deficiency", "iron and zinc"]:
        return "Iron Deficiency"
    if nl in ["zinc", "zinc deficiency"]:
        return "Zinc Deficiency"
    if nl in ["biotin", "biotin b7 deficiency"]:
        return "Biotin B7 Deficiency"
    return n


class MedScanPipeline:
    def __init__(self):
        self.class_map_file = Path("ml/class_maps/image_to_nutrient.json")
        self.mappings: Dict[str, Dict[str, Optional[str]]] = dict(DEFAULT_IMAGE_TO_NUTRIENT)
        self._load_mappings()

    def _load_mappings(self):
        if self.class_map_file.exists():
            try:
                with open(self.class_map_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "models" in data:
                        self.mappings = data["models"]
            except Exception as e:
                logger.warning("Could not load image_to_nutrient.json: %s", e)

    def get_checklist_for_region(self, region: str) -> List[Dict[str, str]]:
        reg_clean = region.lower().strip()
        return REGION_CHECKLIST.get(reg_clean, REGION_CHECKLIST["combined"])

    async def predict_image_via_ml_service(
        self, model_name: str, file_bytes: bytes, filename: str, content_type: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Proxies image prediction to ml-service. Returns (response_dict, error_msg)."""
        url = f"{ML_SERVICE_URL}/predict/image"
        try:
            files = {"file": (filename, file_bytes, content_type)}
            data = {"model_name": model_name}
            async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
                resp = await client.post(url, data=data, files=files)
                if resp.status_code == 200:
                    return resp.json(), None
                return None, f"ML Lab returned error HTTP {resp.status_code}: {resp.text}"
        except httpx.ConnectError:
            return None, "ML Lab service is currently unavailable on port 8001. Running in fallback mode."
        except Exception as e:
            return None, f"Could not connect to ML Lab service: {str(e)}"

    def map_predictions_to_nutrients(
        self, model_name: str, class_predictions: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Maps vision model class percentages to canonical nutrient groups."""
        model_map = self.mappings.get(model_name, {})
        nutrient_evidence: Dict[str, float] = {}

        for item in class_predictions:
            cls = item.get("class_name", "")
            pct = float(item.get("percentage", 0.0))
            nutrient = model_map.get(cls)
            if nutrient:
                norm_nut = normalize_nutrient_key(nutrient)
                if norm_nut not in nutrient_evidence or pct > nutrient_evidence[norm_nut]:
                    nutrient_evidence[norm_nut] = pct

        return nutrient_evidence

    def blend_evidence(
        self,
        image_nutrients: Dict[str, float],
        ticked_symptom_tags: List[str],
        region: Optional[str] = None,
        shortcut_flag: bool = False,
        ml_service_down: bool = False,
    ) -> Dict[str, Any]:
        """Blends image model predictions with reference database symptoms."""
        # Evaluate symptoms via scoring engine
        symptom_result = scoring_service.evaluate_tags(ticked_symptom_tags)
        symptom_nutrients = {
            normalize_nutrient_key(item["nutrient"]): item
            for item in symptom_result.get("nutrient_scores", [])
        }

        # Weighting: 0.25 if shortcut flag, 0.5 normally
        w_img = 0.25 if shortcut_flag else 0.5
        w_sym = 1.0 - w_img

        all_nutrients = set(image_nutrients.keys()) | set(symptom_nutrients.keys())
        blended_scores: List[Dict[str, Any]] = []

        for nut in all_nutrients:
            has_img = nut in image_nutrients
            has_sym = nut in symptom_nutrients

            p_img = image_nutrients.get(nut, 0.0)
            sym_item = symptom_nutrients.get(nut)
            p_sym = sym_item["percentage"] if sym_item else 0.0

            matched_tags = sym_item["matched_tags"] if sym_item else []
            contributing_rows = sym_item["contributing_rows"] if sym_item else []

            if has_img and has_sym:
                raw_blend = (p_img * w_img) + (p_sym * w_sym)
                final_pct = min(95.0, round(raw_blend, 1))
                kind_str = "medscan_blend"
                pct_kind = "MedScan blend %"
                explanation = (
                    f"Blended evidence from Image model % ({p_img}%, weight {w_img}) "
                    f"and Reference match % ({p_sym}%, weight {w_sym:.2f})."
                )
            elif has_img and not has_sym:
                # Image only: capped at 60.0% per spec and labelled 'image only, low reliability'
                raw_pct = min(60.0, round(p_img * w_img, 1))
                final_pct = raw_pct
                kind_str = "image_only"
                pct_kind = "Image model %"
                explanation = "image only, low reliability"
            else:
                # Symptom only (fallback or pure symptom match)
                final_pct = p_sym
                kind_str = "reference_match"
                pct_kind = KIND_REFERENCE_MATCH
                explanation = sym_item.get("percentage_explanation", "Reference database pattern coverage.")

            risk_band = calculate_risk_band(final_pct)

            blended_scores.append({
                "nutrient": nut,
                "percentage": final_pct,
                "percentage_kind": pct_kind,
                "percentage_explanation": explanation,
                "image_percentage": p_img if has_img else None,
                "reference_percentage": p_sym if has_sym else None,
                "risk_band": risk_band,
                "risk_band_label": RISK_BAND_LABEL,
                "matched_tags": matched_tags,
                "contributing_rows": contributing_rows,
                "kind": kind_str,
            })

        # Sort descending by percentage, then nutrient name
        blended_scores.sort(key=lambda x: (-x["percentage"], x["nutrient"]))

        status_str = "MATCHES_FOUND" if blended_scores else "INSUFFICIENT_INFORMATION"
        if ml_service_down:
            msg = "ML Lab service currently unavailable. Displaying symptom reference match results only."
        elif blended_scores:
            msg = f"MedScan analysis generated {len(blended_scores)} nutritional reference patterns."
        else:
            msg = "No nutritional reference patterns identified from the captured image and symptoms."

        return {
            "status": status_str,
            "message": msg,
            "disclaimer": scoring_service.repo.match_symptoms(["dummy"])["disclaimer"],
            "nutrient_scores": blended_scores,
            "matched_entries": symptom_result.get("matched_entries", []),
            "unmatched_user_tags": symptom_result.get("unmatched_user_tags", []),
            "kind": "medscan_blend" if not ml_service_down else "reference_match",
            "shortcut_flag": shortcut_flag,
            "w_img": w_img,
        }


medscan_pipeline = MedScanPipeline()
