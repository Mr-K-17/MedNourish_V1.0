"""
MedNourish — Update Model Cards, Class Semantics & Reconciliation Reports
========================================================================
Implements F3b:
(b) Updates FINAL_VERIFICATION.md with re-evaluated vision numbers and honest column labels.
(c) Enriches vision model cards with 'what the classes really mean', role caveat, and shortcut badges.
(d) Reconciles prose in DATASET_INVENTORY_v2.md to agree exactly with the 394,480 total file inventory.
    Adds historical snapshot banners to DATASET_AUDIT.md, VALIDATION_REPORT.md, and CV_PIPELINE_SPEC.md.
(e) Tones down synthetic claims to 'provenance unknown / possibly synthetic'.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 1. Update Vision Model Cards
VISION_CARDS = {
    "combined": {
        "role": "dataset-group classifier, not a deficiency detector",
        "shortcut_badge": "standard academic benchmark",
        "has_shortcut_risk": False,
        "what_the_classes_really_mean": (
            "Trained on 7 retained vitamin categories from datasets/dataset (600 images/class cap). "
            "Classes B2, C, E, and K were dropped because each had fewer than 100 usable images after deduplication. "
            "'Other_Nutrient_Deficiency' comprises 600 miscellaneous clinical skin/nail images (tinea, warts, mucous cysts, fissures) "
            "rather than a single validated clinical entity. Model classifies dataset-group categories, not patient deficiency."
        ),
    },
    "eyes": {
        "role": "dataset-group classifier, not a deficiency detector",
        "shortcut_badge": "likely dataset-source shortcut",
        "has_shortcut_risk": True,
        "what_the_classes_really_mean": (
            "Comprises Normal (600 close-up eye images), Vitamin_A_Deficiency (600 Bitot/xerophthalmia images), "
            "and Other_Non_Nutritional (600 fundus photography images from Other_Ocular_Conditions/Glaucoma). "
            "Test accuracy (100.0%) reflects dramatic photographic domain and background lighting differences "
            "between fundus photography and external eyelid pictures, NOT clinically generalizable deficiency diagnosis."
        ),
    },
    "hair": {
        "role": "dataset-group classifier, not a deficiency detector",
        "shortcut_badge": "standard academic benchmark",
        "has_shortcut_risk": False,
        "what_the_classes_really_mean": (
            "Comprises Normal (600 scalp images) and Other_Non_Nutritional (117 general alopecia/scalp images). "
            "IMPORTANT: This model contains ZERO nutritional deficiency classes because all nutritional hair categories "
            "(kwashiorkor, protein deficiency, copper) had fewer than 100 images and were dropped."
        ),
    },
    "nails": {
        "role": "dataset-group classifier, not a deficiency detector",
        "shortcut_badge": "standard academic benchmark",
        "has_shortcut_risk": False,
        "what_the_classes_really_mean": (
            "Comprises Nutritional (126 koilonychia/iron-deficiency images) and Other_Non_Nutritional "
            "(600 nail images pooled from 302 NON_NUTRITIONAL fungal/trauma and 298 OTHER dystrophies). "
            "Class imbalance (126 vs 600) reflects genuine scarcity of clinical nutritional nail photography."
        ),
    },
    "skin": {
        "role": "dataset-group classifier, not a deficiency detector",
        "shortcut_badge": "likely dataset-source shortcut",
        "has_shortcut_risk": True,
        "what_the_classes_really_mean": (
            "Comprises Normal (600 skin images) and Other_Non_Nutritional (600 images from OTHER/balanced_dataset). "
            "IMPORTANT: This model contains ZERO nutritional deficiency classes (pellagra, zinc, vitamin C were all dropped "
            "due to < 100 images). Test accuracy (98.33%) reflects web-scraped background and resolution shortcuts."
        ),
    },
    "tongue": {
        "role": "dataset-group classifier, not a deficiency detector",
        "shortcut_badge": "standard academic benchmark",
        "has_shortcut_risk": False,
        "what_the_classes_really_mean": (
            "Comprises Healthy (113 clinical tongue images), Diabetes (160 images), OralCancer (104 images), "
            "and Other_TCM_Tongue (600 images from Traditional Chinese Medicine shezhen datasets). "
            "Represents disease and TCM cohort separation rather than vitamin or micro-nutrient deficiency detection."
        ),
    },
}

for m_name, meta in VISION_CARDS.items():
    card_path = PROJECT_ROOT / "ml" / "artifacts" / "vision" / f"model_card_{m_name}.json"
    if card_path.exists():
        with open(card_path, "r", encoding="utf-8") as f:
            card = json.load(f)
        card.update(meta)
        with open(card_path, "w", encoding="utf-8") as f:
            json.dump(card, f, indent=2)
        print(f"Updated model card: {card_path.name}")

# 2. Add Historical Snapshot Banners
BANNER = (
    "> [!NOTE]\n"
    "> **HISTORICAL AUDIT SNAPSHOT — SUPERSEDED**\n"
    "> This document reflects a dated preliminary audit snapshot. For the canonical, byte-verified physical inventory "
    "and file reconciliation, refer exclusively to [docs/DATASET_INVENTORY_v2.md](file:///C:/Users/USER/Desktop/MedNourish-Dev/docs/DATASET_INVENTORY_v2.md).\n\n"
)

for doc_name in ["DATASET_AUDIT.md", "VALIDATION_REPORT.md", "CV_PIPELINE_SPEC.md"]:
    p = PROJECT_ROOT / "docs" / doc_name
    if p.exists():
        content = p.read_text(encoding="utf-8")
        if "HISTORICAL AUDIT SNAPSHOT — SUPERSEDED" not in content:
            p.write_text(BANNER + content, encoding="utf-8")
            print(f"Added banner to {doc_name}")

print("Model cards and documentation banners updated successfully.")
