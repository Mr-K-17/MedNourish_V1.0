# Code Excerpt: `nursebot_router_webanswer`

- **Repository Path**: [`backend/app/services/nursebot_service.py`](file:///C:\Users\USER\Desktop\MedNourish-Dev/backend/app/services/nursebot_service.py#L1-L30)
- **Lines**: 1–30 (30 lines)
- **Component**: MEDNOURISH Core Implementation

### Architectural Purpose & Design Rationale
Routes user health queries through an emergency triage detector first; if safe, queries the local curated knowledge base and falls back to NIH MedlinePlus REST API with full citation grounding.

```python
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
```

> **Educational Prototype Notice**: MEDNOURISH is an academic research prototype and is not certified as a medical device. Code logic produces nutritional deficiency risk estimates for dietary awareness only.
