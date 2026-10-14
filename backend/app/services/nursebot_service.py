"""Scripted Knowledge Content for App Help & NurseBot (M1B.6).

Adheres strictly to:
- NURSE-01: All content is scripted, deterministic, and listed in one place.
- NURSE-03, NURSE-04, SAF-14: Scripted refusal and redirection patterns for diagnosis,
  medicines, dosages, treatments, and acute conditions.
- Design.md Section 13: Tone and microcopy guidelines.
"""

from typing import Dict, List, Optional
from app.schemas.nursebot import HelpMenuResponse, HelpTopicDetail, HelpTopicSummary

SCRIPTED_HELP_TOPICS: List[Dict] = [
    # 1. App Usage
    {
        "id": "faq_how_medbot_works",
        "category": "app_usage",
        "title": "How does MedBot work?",
        "summary": "Learn how MedBot's Simple and Standard symptom questionnaires function.",
        "is_safety_refusal": False,
        "content": (
            "MedBot is an educational tool that guides you through questions about observable physical signs "
            "across body regions (eyes, hair, lips, tongue, nails, skin). It uses a deterministic rule engine to "
            "compare selected symptoms with reference tables from nutritional literature. It does not use generative AI, "
            "does not diagnose medical conditions, and does not calculate clinical risk scores."
        ),
        "related_actions": ["Open MedBot", "View Symptom Explorer"],
    },
    {
        "id": "faq_how_explorer_works",
        "category": "app_usage",
        "title": "How do I use the Symptom Reference Explorer?",
        "summary": "Understand how to browse and select anatomical symptom tags.",
        "is_safety_refusal": False,
        "content": (
            "The Symptom Reference Explorer allows you to filter symptoms by body region (such as eyes or skin) "
            "and select tags you are curious about. When you run a search, the system identifies reference-table "
            "entries that share those tags. You will see an ordered list showing the exact matched tags and total tags "
            "documented in the reference table."
        ),
        "related_actions": ["Open Symptom Explorer"],
    },
    {
        "id": "faq_careplan_routines",
        "category": "app_usage",
        "title": "What is CarePlan and how do reminders work?",
        "summary": "Understand how to create self-directed daily wellness routines.",
        "is_safety_refusal": False,
        "content": (
            "CarePlan allows you to track self-directed general wellness routines such as drinking water, getting "
            "restful sleep, balanced nutrition, and physical activity. You can check off completed tasks each day. "
            "Please note: In-app reminders only trigger while the application remains open in your active browser window."
        ),
        "related_actions": ["Open CarePlan"],
    },
    {
        "id": "faq_reports_history",
        "category": "app_usage",
        "title": "Where are my past checks saved?",
        "summary": "Access your saved summaries in Files & Reports.",
        "is_safety_refusal": False,
        "content": (
            "When you click 'Save Summary' in MedBot or the Symptom Explorer, a dated snapshot of your reference matches "
            "is saved to your account in 'Files & Reports'. You can view your check-in timeline or delete records at any time. "
            "Saved reports never contain clinical risk scores, probability bands, or diagnostic labels."
        ),
        "related_actions": ["Open Files & Reports"],
    },
    # 2. Privacy & Consent
    {
        "id": "faq_data_privacy",
        "category": "privacy_consent",
        "title": "How is my data handled and protected?",
        "summary": "Information on data minimization, adult consent, and deletion rights.",
        "is_safety_refusal": False,
        "content": (
            "MEDNOURISH follows strict data minimization (C-21). We do not collect your date of birth, age, or real-world "
            "identity documents. All profile data is private to your authenticated account. If you choose to delete your account, "
            "all your profile details, consent records, saved summaries, and CarePlan tasks are permanently erased."
        ),
        "related_actions": ["View Profile Settings"],
    },
    # 3. Educational Scope & Limitations
    {
        "id": "faq_educational_prototype",
        "category": "educational_scope",
        "title": "Why is MedNourish called an Educational Prototype?",
        "summary": "Understanding the prototype status and clinical review boundaries.",
        "is_safety_refusal": False,
        "content": (
            "MEDNOURISH is an academic and educational prototype. The underlying nutritional reference mappings have not "
            "undergone clinical trial verification or formal regulatory review. It is designed to foster health literacy, "
            "not to provide diagnostic conclusions or individualized clinical advice."
        ),
        "related_actions": ["Emergency Help"],
    },
    # 4. Scripted Safety Refusal Patterns (NURSE-03, NURSE-04, SAF-14)
    {
        "id": "refusal_diagnosis",
        "category": "safety_refusals",
        "title": "Can NurseBot diagnose my condition or illness?",
        "summary": "Scripted refusal: NurseBot cannot diagnose illnesses or diseases.",
        "is_safety_refusal": True,
        "content": (
            "No. NurseBot cannot diagnose health conditions, illnesses, or nutritional deficiencies. "
            "Diagnosing a health condition requires a licensed physician or registered dietitian who can examine you, "
            "review your medical history, and order validated clinical laboratory tests (such as serum vitamin panels). "
            "If you are concerned about your symptoms, please consult a qualified clinician."
        ),
        "related_actions": ["Emergency Help"],
    },
    {
        "id": "refusal_medication_dose",
        "category": "safety_refusals",
        "title": "Can NurseBot recommend a medicine, supplement, or dosage?",
        "summary": "Scripted refusal: NurseBot cannot prescribe or recommend medications or dosages.",
        "is_safety_refusal": True,
        "content": (
            "No. I cannot advise on medicines, supplements, or dosages. Supplementation and medications have contraindications, "
            "upper intake limits, and potential interactions with other treatments. A doctor or licensed pharmacist is the only "
            "person who can safely prescribe or recommend dosages appropriate for your specific health profile."
        ),
        "related_actions": ["Emergency Help"],
    },
    {
        "id": "refusal_emergency_urgent",
        "category": "safety_refusals",
        "title": "What should I do if I have chest pain, breathing difficulty, or an acute emergency?",
        "summary": "Scripted redirection: Immediate guidance for acute emergency situations.",
        "is_safety_refusal": True,
        "content": (
            "If you or someone you are with is experiencing severe chest pain, sudden numbness, difficulty breathing, "
            "severe bleeding, or any acute life-threatening symptoms, stop using this application and contact your local "
            "emergency services immediately. You can also tap the 'Need urgent help?' button at any time for crisis guidance. "
            "Do not rely on educational software in an emergency."
        ),
        "related_actions": ["Emergency Help"],
    },
]


import logging
import re
import time
from typing import Dict, List, Optional
from app.schemas.nursebot import (
    HelpMenuResponse,
    HelpTopicDetail,
    HelpTopicSummary,
    NurseBotAskResponse,
)
from app.services.web_answer_service import web_answer_service

logger = logging.getLogger(__name__)


class NurseBotService:
    """Provides scripted app help, deterministic FAQ responses, and factual web reference lookups."""

    def __init__(self):
        self._topics_by_id: Dict[str, Dict] = {t["id"]: t for t in SCRIPTED_HELP_TOPICS}
        self._rate_limits: Dict[str, List[float]] = {}

    def check_rate_limit(self, user_uid: str) -> bool:
        """Returns True if user is within rate limit (10 queries/min), False otherwise."""
        now = time.time()
        cutoff = now - 60.0
        history = self._rate_limits.setdefault(user_uid, [])
        # Purge timestamps older than 60s
        self._rate_limits[user_uid] = [t for t in history if t > cutoff]
        if len(self._rate_limits[user_uid]) >= 10:
            return False
        self._rate_limits[user_uid].append(now)
        return True

    def get_menu(self) -> HelpMenuResponse:
        """Returns the complete list of available scripted help topics grouped by category."""
        categories = sorted(list({t["category"] for t in SCRIPTED_HELP_TOPICS}))
        summaries = [
            HelpTopicSummary(
                id=t["id"],
                category=t["category"],
                title=t["title"],
                summary=t["summary"],
                is_safety_refusal=t.get("is_safety_refusal", False),
            )
            for t in SCRIPTED_HELP_TOPICS
        ]
        return HelpMenuResponse(
            categories=categories,
            topics=summaries,
            disclaimer=(
                "MEDNOURISH NurseBot provides scripted help for using the app. "
                "It is not a real nurse or medical provider and does not give medical advice."
            ),
        )

    def get_topic_detail(self, topic_id: str) -> Optional[HelpTopicDetail]:
        """Retrieves scripted content for a specific topic ID."""
        t = self._topics_by_id.get(topic_id)
        if not t:
            return None

        return HelpTopicDetail(
            id=t["id"],
            category=t["category"],
            title=t["title"],
            summary=t["summary"],
            is_safety_refusal=t.get("is_safety_refusal", False),
            content=t["content"],
            related_actions=t.get("related_actions", []),
        )

    async def ask(self, user_uid: str, question: str) -> NurseBotAskResponse:
        """Processes user question through the intent router:

        1. Emergency check (priority #1)
        2. Personal diagnosis / dosage refusal
        3. Scripted app help Q&A matching
        4. Vitamin / nutrition reference lookups (MedlinePlus web service)
        5. Out-of-scope fallback
        """
        q = question.strip().lower()

        # 1. Emergency Intent (Highest priority!)
        emergency_patterns = [
            r"\bchest\s+pain\b",
            r"\b(?:cannot|cant|can't)\s+breathe\b",
            r"\b(?:difficulty|trouble)\s+breathing\b",
            r"\bshortness\s+of\s+breath\b",
            r"\bsuffocat",
            r"\bsuicid",
            r"\bkill\s+myself\b",
            r"\bwant\s+to\s+die\b",
            r"\bend\s+my\s+life\b",
            r"\bself[\s-]harm\b",
            r"\bsevere\s+bleeding\b",
            r"\bbleeding\s+heavily\b",
            r"\bstroke\b",
            r"\bface\s+drooping\b",
            r"\bheart\s+attack\b",
            r"\bunconscious\b",
            r"\boverdose\b",
        ]
        if any(re.search(pat, q) for pat in emergency_patterns):
            return NurseBotAskResponse(
                reply=(
                    "EMERGENCY ALERT: If you or someone with you is experiencing chest pain, difficulty breathing, "
                    "stroke symptoms, severe bleeding, or thoughts of self-harm, please stop using this app and "
                    "immediately contact your local emergency services (e.g. 911 in US/Canada, 112 in Europe, 999 in UK, "
                    "or call/text 988 for crisis support). Do not wait for software answers in an acute medical emergency."
                ),
                intent="emergency",
                is_web_answer=False,
            )

        # 2. Personal Diagnosis / Dosage Refusal
        refusal_patterns = [
            r"\bdiagnose\s+(?:me|my)\b",
            r"\bwhat\s+(?:illness|disease|condition)\s+do\s+i\s+have\b",
            r"\bdo\s+i\s+have\b",
            r"\btell\s+me\s+what\s+i\s+have\b",
            r"\bam\s+i\s+sick\b",
            r"\bwhat\s+(?:dosage|dose)\b",
            r"\bhow\s+(?:many|much)\s+mg\b",
            r"\bprescribe\b",
            r"\bwhat\s+(?:medicine|pill|drug|medication)\s+should\s+i\s+take\b",
            r"\bhow\s+much\s+should\s+i\s+take\b",
            r"\btreat\s+my\b",
            r"\bcure\s+my\b",
        ]
        if any(re.search(pat, q) for pat in refusal_patterns):
            return NurseBotAskResponse(
                reply="MedNourish does not provide medical diagnoses or dosages; please ask a doctor or pharmacist.",
                intent="refusal",
                is_web_answer=False,
            )

        # 3. Scripted App Help Matching
        app_topic_matchers = [
            ("faq_how_medbot_works", [r"\bmedbot\b", r"\bsymptom\s+check\b", r"\bquestionnaire\b", r"\bsimple\s+and\s+standard\b"]),
            ("faq_how_explorer_works", [r"\bexplorer\b", r"\bsymptom\s+explorer\b", r"\bbrowse\b", r"\btags\b"]),
            ("faq_careplan_routines", [r"\bcareplan\b", r"\broutine\b", r"\bwellness\b", r"\breminders?\b", r"\bhabits?\b"]),
            ("faq_reports_history", [r"\bsaved\s+summar(?:y|ies)\b", r"\breports?\b", r"\bfiles?\b", r"\bpast\s+checks?\b", r"\bdownload\b"]),
            ("faq_data_privacy", [r"\bprivacy\b", r"\bdata\b", r"\bconsent\b", r"\bdelete\s+account\b", r"\berase\b"]),
            ("faq_educational_prototype", [r"\bprototype\b", r"\beducational\b", r"\bclinical\s+trial\b", r"\bregulatory\b"]),
        ]
        for topic_id, patterns in app_topic_matchers:
            if any(re.search(pat, q) for pat in patterns):
                topic = self.get_topic_detail(topic_id)
                if topic:
                    return NurseBotAskResponse(
                        reply=topic.content,
                        intent="app_help",
                        is_web_answer=False,
                    )

        # 4. Vitamin / Nutrition / Reference Question
        nutrition_patterns = [
            r"\bvitamins?\b",
            r"\bminerals?\b",
            r"\bnutrients?\b",
            r"\bdeficienc(?:y|ies)\b",
            r"\bscurvy\b",
            r"\bpellagra\b",
            r"\brickets\b",
            r"\banemia\b",
            r"\bberiberi\b",
            r"\bcheilosis\b",
            r"\bglossitis\b",
            r"\bzinc\b",
            r"\biron\b",
            r"\bcalcium\b",
            r"\bmagnesium\b",
            r"\bpotassium\b",
            r"\biodine\b",
            r"\bfolate\b",
            r"\bfolic\s+acid\b",
            r"\bniacin\b",
            r"\briboflavin\b",
            r"\bthiamin(?:e)?\b",
            r"\bomega[\s-]3\b",
            r"\bfoods?\s+(?:rich\s+in|with|high\s+in)\b",
            r"\bdietary\b",
            r"\bsupplements?\b",
        ]
        if any(re.search(pat, q) for pat in nutrition_patterns):
            web_ans = await web_answer_service.fetch_web_answer(question)
            return NurseBotAskResponse(
                reply=web_ans["reply"] or "Could not reach medical reference services. Please consult a qualified clinician.",
                intent="web_reference",
                source_name=web_ans.get("source_name"),
                source_url=web_ans.get("source_url"),
                is_web_answer=web_ans.get("is_web_answer", False),
            )

        # 5. Out-of-Scope Fallback
        return NurseBotAskResponse(
            reply="I can help with questions about using MedNourish or look up general vitamin and nutrition reference facts. For personal health advice, please consult a qualified clinician.",
            intent="out_of_scope",
            is_web_answer=False,
        )


nursebot_service = NurseBotService()

