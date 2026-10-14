"""MedBot Questionnaire Service.

Implements M1B.4 Guided MedBot Questionnaire:
- Defines stable approved question sets for Simple (yes/no) and Standard (multiple choice) modes.
- Draws symptom options strictly from the curated reference tags in KnowledgeRepository.
- Includes optional, consented general lifestyle/routine context questions per MEDBOT-01, MEDBOT-10, OD-18.
- Guarantees that lifestyle answers NEVER alter symptom tag extraction or matcher scoring.
- Reuses the deterministic set-intersection Reference Matcher Engine (KnowledgeRepository.match_symptoms).
- Provides deterministic evaluation, skip/back/resume predictability, and empty/insufficient handling.
"""

from typing import Dict, List, Optional
from app.schemas.medbot import (
    AnswerSubmission,
    MedBotEvaluateResponse,
    QuestionnaireConfigResponse,
    QuestionnaireQuestion,
    QuestionOption,
)
from app.services.knowledge_service import (
    MATCHER_VERSION,
    PACKAGE_VERSION,
    knowledge_repo,
    normalize_tag,
)

# Standard questions configuration
# Drawn from approved adult nutritional tag vocabulary across 6 regions + general lifestyle
QUESTIONS_DATABASE: List[Dict] = [
    {
        "id": "q_eyes",
        "body_region": "EYES",
        "question_text": "Have you noticed any eye or vision changes recently?",
        "explanation": "Eye discomfort, unusual dryness, and night vision changes are catalogued in nutritional reference literature.",
        "simple_options": [
            {"id": "opt_eyes_yes", "label": "Yes, I notice eye or vision symptoms", "tag": "nightblindness"},
            {"id": "opt_eyes_no", "label": "No eye symptoms", "tag": None, "is_none_or_no": True},
        ],
        "standard_options": [
            {"id": "opt_eyes_dry", "label": "Dry, gritty, or irritated eyes", "tag": "eyedryness"},
            {"id": "opt_eyes_night", "label": "Difficulty seeing in dim light or night blindness", "tag": "nightblindness"},
            {"id": "opt_eyes_blur", "label": "Blurred vision or difficulty focusing", "tag": "blurredvision"},
            {"id": "opt_eyes_light", "label": "Sensitivity to light", "tag": "lightsensitivity"},
            {"id": "opt_eyes_none", "label": "None of these eye symptoms", "tag": None, "is_none_or_no": True},
        ],
    },
    {
        "id": "q_hair",
        "body_region": "HAIR",
        "question_text": "Have you experienced noticeable changes in your hair texture or density?",
        "explanation": "Hair thinning, fragility, and unusual shedding can correlate with several micronutrient levels.",
        "simple_options": [
            {"id": "opt_hair_yes", "label": "Yes, hair thinning, brittle hair, or shedding", "tag": "hairthinning"},
            {"id": "opt_hair_no", "label": "No hair changes", "tag": None, "is_none_or_no": True},
        ],
        "standard_options": [
            {"id": "opt_hair_thin", "label": "Hair thinning or increased shedding", "tag": "hairthinning"},
            {"id": "opt_hair_brittle", "label": "Dry, brittle, or easily breaking hair", "tag": "brittlehair"},
            {"id": "opt_hair_patch", "label": "Patchy hair loss or scalp irritation", "tag": "patchyhairloss"},
            {"id": "opt_hair_diffuse", "label": "Generalized diffuse hair loss", "tag": "diffusehairloss"},
            {"id": "opt_hair_none", "label": "No unusual hair changes", "tag": None, "is_none_or_no": True},
        ],
    },
    {
        "id": "q_lips_mouth",
        "body_region": "LIPS",
        "question_text": "Are you experiencing soreness, cracking, or irritation around your lips?",
        "explanation": "Cracked corners of the mouth and lip inflammation are common clinical signs in reference tables.",
        "simple_options": [
            {"id": "opt_lips_yes", "label": "Yes, sore or cracked lips", "tag": "crackedlips"},
            {"id": "opt_lips_no", "label": "No lip or mouth symptoms", "tag": None, "is_none_or_no": True},
        ],
        "standard_options": [
            {"id": "opt_lips_cracked", "label": "Cracked or peeling corners of the lips", "tag": "crackedlips"},
            {"id": "opt_lips_sore", "label": "Red, painful, or tender lips", "tag": "sorelips"},
            {"id": "opt_lips_dry", "label": "Excessive lip dryness or pale lips", "tag": "paledrylips"},
            {"id": "opt_lips_none", "label": "None of the above", "tag": None, "is_none_or_no": True},
        ],
    },
    {
        "id": "q_tongue",
        "body_region": "TONGUE",
        "question_text": "Do you notice soreness, unusual redness, or a burning sensation on your tongue?",
        "explanation": "Tongue redness (glossitis) and taste changes are frequently documented nutritional indicators.",
        "simple_options": [
            {"id": "opt_tongue_yes", "label": "Yes, tongue soreness or burning", "tag": "soretongue"},
            {"id": "opt_tongue_no", "label": "No tongue symptoms", "tag": None, "is_none_or_no": True},
        ],
        "standard_options": [
            {"id": "opt_tongue_sore", "label": "Sore, inflamed, or swollen tongue", "tag": "soretongue"},
            {"id": "opt_tongue_burn", "label": "Burning sensation or discomfort", "tag": "burningsensation"},
            {"id": "opt_tongue_taste", "label": "Altered sense of taste or metallic taste", "tag": "tastechange"},
            {"id": "opt_tongue_smooth", "label": "Unusually smooth or beefy red tongue", "tag": "smoothtongue"},
            {"id": "opt_tongue_none", "label": "None of the above", "tag": None, "is_none_or_no": True},
        ],
    },
    {
        "id": "q_nails",
        "body_region": "NAILS",
        "question_text": "Have your fingernails become brittle, ridged, or unusually shaped?",
        "explanation": "Nail plate changes such as spooning, ridges, or fragility often reflect mineral and vitamin status.",
        "simple_options": [
            {"id": "opt_nails_yes", "label": "Yes, brittle or peeling nails", "tag": "brittlenails"},
            {"id": "opt_nails_no", "label": "No nail changes", "tag": None, "is_none_or_no": True},
        ],
        "standard_options": [
            {"id": "opt_nails_brittle", "label": "Brittle, splitting, or soft nails", "tag": "brittlenails"},
            {"id": "opt_nails_ridge", "label": "Pronounced vertical or horizontal ridges", "tag": "nailridging"},
            {"id": "opt_nails_spoon", "label": "Thin, concave, or spoon-shaped nails", "tag": "spoonshapednails"},
            {"id": "opt_nails_spots", "label": "Small red or dark bleeding spots under nails", "tag": "nailbleedingspots"},
            {"id": "opt_nails_none", "label": "No unusual nail changes", "tag": None, "is_none_or_no": True},
        ],
    },
    {
        "id": "q_skin",
        "body_region": "SKIN",
        "question_text": "Are you experiencing unusual skin dryness, rough patches, or persistent rashes?",
        "explanation": "Dermatological signs like follicular roughness, bruising, and scaling appear across multiple reference classes.",
        "simple_options": [
            {"id": "opt_skin_yes", "label": "Yes, rough skin, bruising, or rashes", "tag": "dryskin"},
            {"id": "opt_skin_no", "label": "No skin symptoms", "tag": None, "is_none_or_no": True},
        ],
        "standard_options": [
            {"id": "opt_skin_dry", "label": "Persistent rough, scaly, or dry skin", "tag": "dryskin"},
            {"id": "opt_skin_bruise", "label": "Easy bruising or slow-healing scrapes", "tag": "easybruising"},
            {"id": "opt_skin_itch", "label": "Itching or red skin rashes", "tag": "itching"},
            {"id": "opt_skin_dark", "label": "Darkened or peeling skin patches", "tag": "darkenedskinpatches"},
            {"id": "opt_skin_none", "label": "No skin concerns", "tag": None, "is_none_or_no": True},
        ],
    },
    {
        "id": "q_general_energy",
        "body_region": "GENERAL",
        "question_text": "Do you feel persistent fatigue, weakness, or unexplained sluggishness?",
        "explanation": "General fatigue and weakness are highly prevalent systemic markers across iron and B-vitamin references.",
        "simple_options": [
            {"id": "opt_gen_yes", "label": "Yes, persistent fatigue or low energy", "tag": "fatigue"},
            {"id": "opt_gen_no", "label": "No persistent fatigue", "tag": None, "is_none_or_no": True},
        ],
        "standard_options": [
            {"id": "opt_gen_fatigue", "label": "Daily fatigue not relieved by sleep", "tag": "fatigue"},
            {"id": "opt_gen_weak", "label": "General muscle weakness or lethargy", "tag": "weakness"},
            {"id": "opt_gen_dizzy", "label": "Lightheadedness or dizziness on standing", "tag": "dizziness"},
            {"id": "opt_gen_cold", "label": "Unusual sensitivity to cold", "tag": "coldintolerance"},
            {"id": "opt_gen_none", "label": "Energy levels feel normal", "tag": None, "is_none_or_no": True},
        ],
    },
    # Optional lifestyle & dietary context question (MEDBOT-01, MEDBOT-10, OD-18)
    # Stored for user context only; STRICTLY EXCLUDED from symptom matching
    {
        "id": "q_lifestyle_routine",
        "body_region": "GENERAL",
        "question_text": "Optional: How would you describe your typical daily routine and sun exposure?",
        "explanation": "Lifestyle context helps inform personal reflection. Answers to this question are strictly educational and NEVER influence your symptom matches.",
        "is_lifestyle": True,
        "simple_options": [
            {"id": "opt_life_indoor", "label": "Mostly indoor desk work / minimal direct sunlight", "tag": None},
            {"id": "opt_life_outdoor", "label": "Regular outdoor activity and sunlight", "tag": None},
            {"id": "opt_life_skip", "label": "Prefer not to share", "tag": None, "is_none_or_no": True},
        ],
        "standard_options": [
            {"id": "opt_life_std_desk", "label": "Predominantly indoors (under 15 mins daily sun exposure)", "tag": None},
            {"id": "opt_life_std_diet", "label": "Vegetarian or vegan dietary preferences", "tag": None},
            {"id": "opt_life_std_active", "label": "High physical exertion / regular endurance training", "tag": None},
            {"id": "opt_life_std_balanced", "label": "Balanced routine with mixed diet and daily sunlight", "tag": None},
            {"id": "opt_life_std_skip", "label": "Skip lifestyle context", "tag": None, "is_none_or_no": True},
        ],
    },
]


class MedBotService:
    """Orchestrates MedBot questionnaires and deterministic evaluation."""

    def __init__(self):
        self._questions = QUESTIONS_DATABASE

    def get_questionnaire_config(self, mode: str = "simple") -> QuestionnaireConfigResponse:
        """Constructs ordered question configuration for Simple or Standard mode."""
        norm_mode = mode.lower().strip()
        if norm_mode not in ("simple", "standard"):
            norm_mode = "simple"

        formatted_questions: List[QuestionnaireQuestion] = []
        for idx, q_data in enumerate(self._questions, start=1):
            raw_options = q_data["simple_options"] if norm_mode == "simple" else q_data["standard_options"]
            options = [
                QuestionOption(
                    id=opt["id"],
                    label=opt["label"],
                    tag=opt.get("tag"),
                    is_none_or_no=opt.get("is_none_or_no", False),
                )
                for opt in raw_options
            ]

            formatted_questions.append(
                QuestionnaireQuestion(
                    id=q_data["id"],
                    step_number=idx,
                    body_region=q_data["body_region"],
                    question_text=q_data["question_text"],
                    explanation=q_data.get("explanation"),
                    mode_availability=["simple", "standard"],
                    is_optional=True,
                    is_lifestyle=q_data.get("is_lifestyle", False),
                    allow_multiple=(norm_mode == "standard" and not q_data.get("is_lifestyle", False)),
                    options=options,
                )
            )

        disclaimer = (
            "MEDNOURISH is an educational prototype. Results are reference-table matches and general health education, "
            "never medical diagnoses, predictions, or risk assessments. Discuss any symptom concerns with a qualified clinician."
        )

        return QuestionnaireConfigResponse(
            mode=norm_mode,
            total_steps=len(formatted_questions),
            disclaimer=disclaimer,
            questions=formatted_questions,
            package_version=PACKAGE_VERSION,
            matcher_version=MATCHER_VERSION,
        )

    def evaluate_answers(
        self,
        mode: str,
        answers: List[AnswerSubmission],
        confirmed_free_text_tags: Optional[List[str]] = None,
    ) -> MedBotEvaluateResponse:
        """Extracts symptom tags and performs deterministic matching.

        Adheres strictly to:
        - MEDBOT-03: Only cleaned symptom tags feed the matcher.
        - MEDBOT-10: Lifestyle responses do NOT alter matches.
        - SAF-06: Empty or zero matches return INSUFFICIENT_INFORMATION.
        - Deterministic parity with Symptom Explorer (same tags = identical output).
        - C-33 / Phase 2: Incorporates confirmed free-text extraction tags.
        """
        extracted_tags: Set[str] = set()
        lifestyle_data: Dict[str, List[str]] = {}

        # 1. Include confirmed free text tags if present
        if confirmed_free_text_tags:
            for t in confirmed_free_text_tags:
                norm_t = normalize_tag(t)
                if norm_t:
                    extracted_tags.add(norm_t)

        # Index question database by id
        q_map = {q["id"]: q for q in self._questions}

        for ans in answers:
            if ans.skipped:
                continue

            q = q_map.get(ans.question_id)
            if not q:
                continue

            options_list = q["simple_options"] if mode == "simple" else q["standard_options"]
            opt_by_id = {opt["id"]: opt for opt in options_list}

            is_lifestyle = q.get("is_lifestyle", False)

            for opt_id in ans.selected_option_ids:
                opt = opt_by_id.get(opt_id)
                if not opt:
                    continue

                if is_lifestyle:
                    lifestyle_data.setdefault(ans.question_id, []).append(opt["label"])
                else:
                    tag = opt.get("tag")
                    if tag and not opt.get("is_none_or_no", False):
                        norm_tag = normalize_tag(tag)
                        if norm_tag:
                            extracted_tags.add(norm_tag)

        # Delegate matching directly to scoring_service for Reference match % and noisy-OR nutrient groups
        from app.services.scoring_service import scoring_service
        sorted_user_tags = sorted(list(extracted_tags))
        match_result = scoring_service.evaluate_tags(user_tags=sorted_user_tags, region_filter=None)

        return MedBotEvaluateResponse(
            status=match_result["status"],
            message=match_result["message"],
            disclaimer=match_result["disclaimer"],
            collected_symptom_tags=sorted_user_tags,
            lifestyle_responses=lifestyle_data,
            nutrient_scores=match_result.get("nutrient_scores", []),
            matched_entries=match_result.get("matched_entries", []),
            unmatched_user_tags=match_result.get("unmatched_user_tags", []),
            package_version=PACKAGE_VERSION,
            matcher_version=MATCHER_VERSION,
            review_status="unreviewed draft",
        )


# Global singleton service
medbot_service = MedBotService()
