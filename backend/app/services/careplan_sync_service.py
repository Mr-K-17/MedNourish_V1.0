"""CarePlan Auto-Sync Service from Assessment Reports (Phase 5).

Guarantees:
- Syncs top 2 nutrients with percentage >= 30 into actionable wellness routines.
- Strictly uses curated non-medication columns: Dietary_Recommendations, Lifestyle_Routine, Follow_Up_Recommendation.
- STRICTLY EXCLUDES Suggested_Supplementation and drug/dosage terms.
- Strips timeframes and medication terms.
- Flagged auto=True with source_entry_id and de-duplicated by (nutrient, text_hash).
- Marks items stale when nutrient falls below 30.
- NEVER deletes user-created (auto=False) or user-edited (is_user_edited=True) items.
- High risk band automatically adds a 'consult a qualified clinician' item.
"""

import csv
import hashlib
import logging
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.user import CarePlanItem

logger = logging.getLogger(__name__)

CURATED_ROUTINE_DIR = Path("knowledge/curated")


def clean_routine_text(raw_text: str) -> str:
    """Strips timeframes, supplement/drug keywords, and truncates to 140 chars."""
    if not raw_text:
        return ""
    text = raw_text.strip()

    # Strip timeframe phrases
    timeframe_patterns = [
        r"\b(?:within|for|every)\s+\d+[\s-]*(?:days?|weeks?|months?|years?)\b",
        r"\b\d+[\s-]*(?:days?|weeks?|months?|years?)\b",
        r"\b(?:daily|weekly|monthly)\s+for\s+\d+\s+(?:days?|weeks?|months?)\b",
        r"\bevery\s+\d+[\s-]*\d*\s*(?:months?|weeks?)\b",
        r"\broutine\s+eye\s+exam\s+every\s+\d+\s+months\b",
        r"\bperiodic\s+nutritional\s+panel\s+every\s+\d+[\s-]*\d*\s+months\b",
    ]
    for pat in timeframe_patterns:
        text = re.sub(pat, "", text, flags=re.IGNORECASE)

    # Strip supplement, drug, dosage terms
    drug_patterns = [
        r"\b(?:supplementation|supplements?|dosage|dosing|medications?|oral retinol|pills?|injections?|prescribed)\b",
        r"\bhigh-dose\s+therapeutic\b",
        r"\bmaintenance\s+dosing\b",
        r"\bmultivitamin\b",
    ]
    for pat in drug_patterns:
        text = re.sub(pat, "", text, flags=re.IGNORECASE)

    # Clean whitespace and trailing punctuation
    text = re.sub(r"\s+", " ", text).strip(" ,;.-")
    if len(text) > 135:
        # Truncate at word boundary
        cutoff = text[:135].rfind(" ")
        if cutoff > 50:
            text = text[:cutoff]
        else:
            text = text[:135]
    return text.strip()


def get_curated_routines_for_nutrient(nutrient_name: str) -> List[Dict[str, str]]:
    """Scans curated CSVs for matching nutrient and returns cleaned non-medication recommendations."""
    results: List[Dict[str, str]] = []
    if not CURATED_ROUTINE_DIR.exists():
        return results

    norm_nut = nutrient_name.lower().replace("deficiency", "").strip()

    for csv_file in CURATED_ROUTINE_DIR.glob("*_Suggested_Routine.csv"):
        try:
            with open(csv_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    vit_def = row.get("Vitamin_Deficiency", "").lower()
                    assoc_vit = row.get("Associated_Vitamin", "").lower()

                    if norm_nut in vit_def or norm_nut in assoc_vit:
                        # 1. Dietary recommendation is now handled by the deterministic MealPlan service (C-39).
                        # Stop creating one-line food items.

                        # 2. Lifestyle routine (lifestyle / general)
                        lifestyle = row.get("Lifestyle_Routine", "")
                        clean_life = clean_routine_text(lifestyle)
                        if clean_life and len(clean_life) >= 12:
                            results.append({
                                "category": "general",
                                "title": f"Habit: {clean_life}",
                            })

                        # 3. Follow-up recommendation (general)
                        followup = row.get("Follow_Up_Recommendation", "")
                        clean_follow = clean_routine_text(followup)
                        if clean_follow and len(clean_follow) >= 12:
                            results.append({
                                "category": "general",
                                "title": f"Guidance: {clean_follow}",
                            })
                        if len(results) >= 2:
                            break
        except Exception as e:
            logger.debug(f"Error reading routine file {csv_file}: {e}")

    return results


def sync_careplan_from_top_nutrients(
    db: Session,
    user_id: str,
    source_entry_id: str,
    top_nutrients: List[Dict],
    max_risk_band: str,
) -> Dict[str, int]:
    """Syncs curated routine tasks for top nutrients >= 30% into CarePlan with de-duplication and stale tracking."""
    # Filter top 2 nutrients with percentage >= 30
    eligible_nutrients = [n for n in top_nutrients if n.get("final_pct", 0) >= 30.0][:2]
    active_nutrient_names = {n.get("nutrient", "") for n in eligible_nutrients if n.get("nutrient")}

    created_count = 0
    reactivated_count = 0
    stale_count = 0

    # Mark old auto food items stale (never delete user-created or user-edited items per C-39)
    old_auto_foods = (
        db.query(CarePlanItem)
        .filter(
            CarePlanItem.user_id == user_id,
            CarePlanItem.is_auto.is_(True),
            CarePlanItem.category == "food",
            CarePlanItem.is_user_edited.is_(False),
            CarePlanItem.is_stale.is_(False),
        )
        .all()
    )
    for it in old_auto_foods:
        it.is_stale = True
        stale_count += 1

    # 1. Process items for each eligible nutrient
    for nut_item in eligible_nutrients:
        nut_name = nut_item.get("nutrient", "")
        if not nut_name:
            continue

        routines = get_curated_routines_for_nutrient(nut_name)
        if not routines:
            # Fallback lifestyle routine
            routines = [{
                "category": "general",
                "title": f"Habit: Maintain daily balanced wellness routine for {nut_name}",
            }]

        for r in routines[:2]:  # at most 2 items per nutrient
            title = r["title"][:140]
            cat = r["category"]
            text_hash = hashlib.sha256(title.lower().strip().encode("utf-8")).hexdigest()[:16]

            # Check if existing item exists
            existing = (
                db.query(CarePlanItem)
                .filter(
                    CarePlanItem.user_id == user_id,
                    CarePlanItem.nutrient == nut_name,
                    CarePlanItem.text_hash == text_hash,
                )
                .first()
            )

            if existing:
                if existing.is_stale and not existing.is_user_edited:
                    existing.is_stale = False
                    reactivated_count += 1
            else:
                new_item = CarePlanItem(
                    id=f"cpt_{uuid.uuid4().hex[:16]}",
                    user_id=user_id,
                    title=title,
                    category=cat,
                    target_frequency="daily",
                    reminder_time=None,
                    is_completed=False,
                    is_auto=True,
                    source_entry_id=source_entry_id,
                    nutrient=nut_name,
                    text_hash=text_hash,
                    is_stale=False,
                    is_user_edited=False,
                    created_at=datetime.utcnow(),
                )
                db.add(new_item)
                created_count += 1

    # 2. If High risk band: add clinician consultation notice item
    if "high" in max_risk_band.lower():
        active_nutrient_names.add("Clinical Follow-Up")
        clinician_title = "Schedule an appointment with a doctor or dietitian regarding physical signs"
        clin_hash = hashlib.sha256(clinician_title.lower().encode("utf-8")).hexdigest()[:16]

        existing_clin = (
            db.query(CarePlanItem)
            .filter(
                CarePlanItem.user_id == user_id,
                CarePlanItem.nutrient == "Clinical Follow-Up",
                CarePlanItem.text_hash == clin_hash,
            )
            .first()
        )
        if existing_clin:
            if existing_clin.is_stale:
                existing_clin.is_stale = False
                reactivated_count += 1
        else:
            clin_item = CarePlanItem(
                id=f"cpt_{uuid.uuid4().hex[:16]}",
                user_id=user_id,
                title=clinician_title,
                category="general",
                target_frequency="once",
                reminder_time=None,
                is_completed=False,
                is_auto=True,
                source_entry_id=source_entry_id,
                nutrient="Clinical Follow-Up",
                text_hash=clin_hash,
                is_stale=False,
                is_user_edited=False,
                created_at=datetime.utcnow(),
            )
            db.add(clin_item)
            created_count += 1

    # 3. Mark stale for auto items whose nutrients are no longer in top nutrients
    existing_auto_items = (
        db.query(CarePlanItem)
        .filter(
            CarePlanItem.user_id == user_id,
            CarePlanItem.is_auto.is_(True),
            CarePlanItem.is_user_edited.is_(False),
            CarePlanItem.is_stale.is_(False),
        )
        .all()
    )

    for item in existing_auto_items:
        if item.nutrient and item.nutrient not in active_nutrient_names:
            item.is_stale = True
            stale_count += 1

    # Trigger MealPlan deterministic regeneration (C-39)
    try:
        from app.services.meal_plan_service import sync_meal_plan_from_report
        sync_meal_plan_from_report(db, user_id, source_entry_id, top_nutrients)
    except Exception as e:
        logger.warning("CarePlan v3 meal plan sync failed non-fatally: %s", e)

    db.commit()
    return {
        "created": created_count,
        "reactivated": reactivated_count,
        "stale": stale_count,
    }
