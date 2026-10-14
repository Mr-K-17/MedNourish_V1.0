# MedNourish — Tabular Symptom/Lifestyle Model Feature Mapping Specification

Module: `ml/service/app.py` & `backend/app/api/v1/mllab.py`  
Artifact: `ml/artifacts/tabular/model_card_main_symptom_lifestyle_only.json`  
Spec: Phase 5(a) Tabular Profile Predictor  

---

## 1. Overview

The `symptom_lifestyle_only` model profile trains non-invasive tabular predictors (XGBoost & LightGBM) to estimate multi-class syndrome probabilities across 5 target classes:
- **`Healthy`**
- **`Anemia`**
- **`Rickets_Osteomalacia`**
- **`Night_Blindness`**
- **`Scurvy`**

All returned class probabilities are explicitly labeled **`'Model % (trained on unverified data)'`** and map syndromes to nutrients solely as **supporting evidence**.

---

## 2. Feature Specification (18 Input Dimensions)

| Feature Name | Category | Training Default / Median | Description & Extraction Rule | Flag When Missing |
|:---|:---:|:---:|:---|:---:|
| `gender` | Categorical | `"Female"` | From user profile (`gender`). | `'estimated'` |
| `smoking_status` | Categorical | `"Non-Smoker"` | From profile / questionnaire habit. | `'estimated'` |
| `alcohol_consumption` | Categorical | `"None"` | From profile / questionnaire habit. | `'estimated'` |
| `exercise_level` | Categorical | `"Moderate"` | From profile / questionnaire habit. | `'estimated'` |
| `diet_type` | Categorical | `"Balanced"` | From profile / questionnaire habit. | `'estimated'` |
| `sun_exposure` | Categorical | `"Moderate"` | From profile / questionnaire habit. | `'estimated'` |
| `income_level` | Categorical | `"Middle"` | Baseline demographic assumption. | `'estimated'` |
| `latitude_region` | Categorical | `"Temperate"` | Baseline geographic assumption. | `'estimated'` |
| `age` | Demographic | `50.77` years | From user profile (`age`). | `'estimated'` |
| `bmi` | Demographic | `26.11` kg/m² | From user profile (`bmi` or height/weight). | `'estimated'` |
| `has_night_blindness` | Symptom | `0` (False) | 1 if tags match: *night blindness, dark adaptation, bitot's spots, xerophthalmia*. | — |
| `has_fatigue` | Symptom | `0` (False) | 1 if tags match: *fatigue, tiredness, lethargy, exhaustion, weakness*. | — |
| `has_bleeding_gums` | Symptom | `0` (False) | 1 if tags match: *bleeding gums, swollen gums, spongy gums, gingivitis*. | — |
| `has_bone_pain` | Symptom | `0` (False) | 1 if tags match: *bone pain, joint pain, aching bones, skeletal pain*. | — |
| `has_muscle_weakness` | Symptom | `0` (False) | 1 if tags match: *muscle weakness, muscle cramps, weak muscles, myopathy*. | — |
| `has_numbness_tingling`| Symptom | `0` (False) | 1 if tags match: *numbness, tingling, paresthesia, pins and needles, neuropathy*. | — |
| `has_memory_problems` | Symptom | `0` (False) | 1 if tags match: *memory problems, brain fog, cognitive difficulty, confusion*. | — |
| `has_pale_skin` | Symptom | `0` (False) | 1 if tags match: *pale skin, pallor, pale conjunctiva, paleness*. | — |

---

## 3. Syndrome-to-Nutrient Supporting Evidence Crosswalk

Syndromes predicted by the tabular model are never clinical diagnostic conclusions; they provide supporting evidence for canonical nutritional reference tables:

| Predicted Syndrome | Supporting Evidence Nutrients | Exact Output Wording |
|:---|:---|:---|
| **`Anemia`** | Iron, Vitamin B12, Folate | `"supporting evidence: Anemia -> Iron / Vitamin B12 / Folate"` |
| **`Rickets_Osteomalacia`** | Vitamin D, Calcium | `"supporting evidence: Rickets -> Vitamin D"` |
| **`Night_Blindness`** | Vitamin A | `"supporting evidence: Night Blindness -> Vitamin A"` |
| **`Scurvy`** | Vitamin C | `"supporting evidence: Scurvy -> Vitamin C"` |
| **`Healthy`** | Baseline | `"supporting evidence: Healthy -> Baseline nutritional adequacy"` |

---

## 4. Probabilistic Blending & Consensus

For each syndrome $k \in \{0, \dots, 4\}$:
$$p_{\text{consensus}}(k) = \frac{p_{\text{xgb}}(k) + p_{\text{lgb}}(k)}{2}$$

Both individual percentages and the blended consensus percentage are returned and rounded to 1 decimal place.
