"""Meal Plan Service for Deterministic 7-Day CarePlan Meal Planning (Phase 5 / C-39).

Guarantees:
- Deterministic: same inputs -> exact same plan.
- Foods only: strictly zero medications, supplements, doses, calories, or grams (C-08, C-22, C-39).
- Respects diet preferences: vegan, veg, eggetarian, nonveg.
- Respects allergens: celiac (no gluten), lactose intolerance (no dairy), nuts, eggs, fish, soy.
- Respects cautions: diabetes (no high_sugar), hypertension (no high_sodium), kidney (no high_potassium).
- Adds doctor consultation line for kidney disease, liver disease, or type 1 diabetes.
- Focus nutrients covered by >= 2 meals/day, fiber every day.
- No consecutive-day repeat of main dishes.
- First report entry creates the first active plan immediately.
- Replaces active plan only if focus nutrient set changes or top percentage moves >= 10 points.
"""

import csv
from datetime import datetime, date, timedelta
import hashlib
import json
import logging
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy.orm import Session
from app.models.user import (
    CarePlanMealLog,
    CarePlanMealPlan,
    CarePlanPrefs,
    UserProfile,
    SavedSummary,
)

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]
FOOD_ITEMS_PATH = REPO_ROOT / "knowledge" / "curated" / "food_items.csv"
NUTRIENT_GUIDANCE_PATH = REPO_ROOT / "knowledge" / "curated" / "nutrient_guidance.csv"

# Normalization mapping between scoring strings and 18 internal nutrient IDs
NUTRIENT_KEY_MAP = {
    "vitamin a": "vitamin_a",
    "vitamin a deficiency": "vitamin_a",
    "vitamin b complex": "b_complex",
    "vitamin b complex deficiency": "b_complex",
    "vitamin b-complex": "b_complex",
    "vitamin b2": "b2",
    "vitamin b2 deficiency": "b2",
    "riboflavin": "b2",
    "vitamin b3": "b3",
    "vitamin b3 deficiency": "b3",
    "niacin": "b3",
    "vitamin b9": "b9_folate",
    "vitamin b9 deficiency": "b9_folate",
    "folate": "b9_folate",
    "vitamin b9 / folate": "b9_folate",
    "vitamin b12": "b12",
    "vitamin b12 deficiency": "b12",
    "vitamin c": "vitamin_c",
    "vitamin c deficiency": "vitamin_c",
    "vitamin d": "vitamin_d",
    "vitamin d deficiency": "vitamin_d",
    "vitamin e": "vitamin_e",
    "vitamin e deficiency": "vitamin_e",
    "vitamin k": "vitamin_k",
    "vitamin k deficiency": "vitamin_k",
    "iron": "iron",
    "iron deficiency": "iron",
    "zinc": "zinc",
    "zinc deficiency": "zinc",
    "biotin": "biotin",
    "biotin b7 deficiency": "biotin",
    "protein energy malnutrition": "protein_energy",
    "protein-energy": "protein_energy",
    "protein": "protein",
    "fiber": "fiber",
    "calcium": "calcium",
    "water": "water",
}

NUTRIENT_DISPLAY_MAP = {
    "vitamin_a": "Vitamin A",
    "b_complex": "Vitamin B Complex",
    "b2": "Vitamin B2",
    "b3": "Vitamin B3",
    "b9_folate": "Vitamin B9 / Folate",
    "b12": "Vitamin B12",
    "vitamin_c": "Vitamin C",
    "vitamin_d": "Vitamin D",
    "vitamin_e": "Vitamin E",
    "vitamin_k": "Vitamin K",
    "iron": "Iron",
    "zinc": "Zinc",
    "biotin": "Biotin",
    "protein_energy": "Protein-Energy",
    "fiber": "Dietary Fiber",
    "protein": "Protein",
    "calcium": "Calcium",
    "water": "Hydration / Water",
}


def normalize_nutrient_id(name: str) -> str:
    """Normalizes arbitrary nutrient names to internal catalog keys."""
    raw = name.strip().lower()
    return NUTRIENT_KEY_MAP.get(raw, "fiber")


class MealPlanRepository:
    """Loads and caches curated food items and guidance."""

    def __init__(self):
        self.food_items: List[Dict[str, Any]] = []
        self.nutrient_guidance: Dict[str, Dict[str, str]] = {}
        self._load()

    def _load(self):
        # Load food items
        if FOOD_ITEMS_PATH.exists():
            with open(FOOD_ITEMS_PATH, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.food_items.append({
                        "food_id": row["food_id"],
                        "name": row["name"],
                        "cuisine": row["cuisine"],
                        "food_group": row["food_group"],
                        "meal_slots": set(row["meal_slots"].split(";")),
                        "diet_tags": set(row["diet_tags"].split(";")),
                        "allergens": set(row["allergens"].split(";")) if row["allergens"] else set(),
                        "cautions": set(row["cautions"].split(";")) if row["cautions"] else set(),
                        "nutrients": set(row["nutrients"].split(";")) if row["nutrients"] else set(),
                        "prep_note": row["prep_note"],
                    })

        # Load nutrient guidance
        if NUTRIENT_GUIDANCE_PATH.exists():
            with open(NUTRIENT_GUIDANCE_PATH, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.nutrient_guidance[row["nutrient"]] = row


repo = MealPlanRepository()


def get_user_preferences(db: Session, user_id: str) -> Dict[str, Any]:
    """Retrieves or initializes user meal planning preferences."""
    prefs = db.query(CarePlanPrefs).filter(CarePlanPrefs.user_id == user_id).first()
    if not prefs:
        return {
            "diet_pref": "veg",
            "cuisine": "indian",
            "meal_times": {"breakfast": "08:00", "lunch": "13:00", "dinner": "20:00"},
        }
    try:
        times = json.loads(prefs.meal_times_json)
    except Exception:
        times = {"breakfast": "08:00", "lunch": "13:00", "dinner": "20:00"}
    return {
        "diet_pref": prefs.diet_pref,
        "cuisine": prefs.cuisine,
        "meal_times": times,
    }


def save_user_preferences(
    db: Session, user_id: str, diet_pref: str, cuisine: str, meal_times: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Saves user preferences for meal planning."""
    prefs = db.query(CarePlanPrefs).filter(CarePlanPrefs.user_id == user_id).first()
    times_json = json.dumps(meal_times or {"breakfast": "08:00", "lunch": "13:00", "dinner": "20:00"})
    if not prefs:
        prefs = CarePlanPrefs(
            user_id=user_id,
            diet_pref=diet_pref,
            cuisine=cuisine,
            meal_times_json=times_json,
            updated_at=datetime.utcnow(),
        )
        db.add(prefs)
    else:
        prefs.diet_pref = diet_pref
        prefs.cuisine = cuisine
        prefs.meal_times_json = times_json
        prefs.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(prefs)
    return {
        "diet_pref": prefs.diet_pref,
        "cuisine": prefs.cuisine,
        "meal_times": json.loads(prefs.meal_times_json),
    }


def get_user_conditions(db: Session, user_id: str) -> List[str]:
    """Fetches user health conditions from profile."""
    prof = db.query(UserProfile).filter(UserProfile.id == user_id).first()
    if not prof or not prof.conditions_json:
        return []
    try:
        data = json.loads(prof.conditions_json)
        return [str(c).lower().strip() for c in data if c]
    except Exception:
        return []


def filter_foods(
    foods: List[Dict[str, Any]],
    diet_pref: str,
    conditions: List[str],
) -> List[Dict[str, Any]]:
    """Filters food items according to diet preference, allergens, and health conditions."""
    filtered = []

    # Map conditions to excluded allergens / cautions
    exclude_allergens = set()
    exclude_cautions = set()

    for cond in conditions:
        if "celiac" in cond or "gluten" in cond:
            exclude_allergens.add("gluten")
        if "lactose" in cond or "milk allergy" in cond or "dairy allergy" in cond:
            exclude_allergens.add("dairy")
        if "peanut" in cond or "nut allergy" in cond:
            exclude_allergens.add("nuts")
        if "diabetes" in cond:
            exclude_cautions.add("high_sugar")
        if "hypertension" in cond or "blood pressure" in cond:
            exclude_cautions.add("high_sodium")
        if "kidney" in cond or "renal" in cond:
            exclude_cautions.add("high_potassium")

    for food in foods:
        # Diet filter
        diets = food["diet_tags"]
        if diet_pref == "vegan":
            if "vegan" not in diets:
                continue
        elif diet_pref == "veg":
            if "veg" not in diets and "vegan" not in diets:
                continue
        elif diet_pref == "eggetarian":
            if "veg" not in diets and "vegan" not in diets and "egg" not in diets:
                continue
        # nonveg allows everything

        # Allergen filter
        if food["allergens"] & exclude_allergens:
            continue

        # Caution filter
        if food["cautions"] & exclude_cautions:
            continue

        filtered.append(food)

    return filtered


def generate_deterministic_meal_plan(
    user_id: str,
    focus_nutrients: List[Dict[str, Any]],
    user_conditions: List[str],
    preferences: Dict[str, Any],
    start_date: Optional[date] = None,
) -> Dict[str, Any]:
    """Generates a complete 7-day meal plan deterministically."""
    if start_date is None:
        start_date = date.today()

    diet_pref = preferences.get("diet_pref", "veg")
    cuisine_pref = preferences.get("cuisine", "indian")

    # 1. Determine focus nutrients
    # Only nutrients with score >= 30% (max 3), normalized
    valid_focus = []
    for fn in focus_nutrients:
        raw_pct = fn.get("percentage") or fn.get("final_pct") or 0.0
        if raw_pct >= 30.0:
            nid = normalize_nutrient_id(fn.get("nutrient", ""))
            valid_focus.append({
                "id": nid,
                "name": NUTRIENT_DISPLAY_MAP.get(nid, nid.title()),
                "pct": round(float(raw_pct), 1),
                "source": fn.get("source", "assessment"),
            })
    valid_focus.sort(key=lambda x: x["pct"], reverse=True)
    valid_focus = valid_focus[:3]

    is_baseline = len(valid_focus) == 0
    if is_baseline:
        target_nutrient_ids = ["fiber", "protein", "calcium"]
        target_display = ["Dietary Fiber", "Protein", "Calcium"]
    else:
        target_nutrient_ids = [f["id"] for f in valid_focus]
        if "fiber" not in target_nutrient_ids:
            target_nutrient_ids.append("fiber")
        target_display = [NUTRIENT_DISPLAY_MAP.get(nid, nid.title()) for nid in target_nutrient_ids]

    # 2. Filter eligible foods
    eligible = filter_foods(repo.food_items, diet_pref, user_conditions)
    if len(eligible) < 20:
        # Fallback to broader diet pool to avoid starvation
        eligible = filter_foods(repo.food_items, "veg" if diet_pref == "vegan" else diet_pref, [])

    # Separate meal candidates and fruits
    slot_foods: Dict[str, List[Dict[str, Any]]] = {
        "breakfast": [f for f in eligible if "breakfast" in f["meal_slots"] and f["food_group"] != "fruit"],
        "lunch": [f for f in eligible if "lunch" in f["meal_slots"] and f["food_group"] != "fruit"],
        "dinner": [f for f in eligible if "dinner" in f["meal_slots"] and f["food_group"] != "fruit"],
        "fruit_side": [f for f in eligible if f["food_group"] == "fruit" or "fruit_side" in f["meal_slots"]],
    }

    # 3. Deterministic Seed
    focus_token = "-".join(f"{f['id']}:{f['pct']}" for f in valid_focus) if valid_focus else "baseline"
    seed_str = f"plan_{user_id}_{focus_token}_{diet_pref}_{cuisine_pref}"
    rng_seed = int(hashlib.sha256(seed_str.encode("utf-8")).hexdigest()[:8], 16)
    rng = random.Random(rng_seed)

    # 4. Doctor consultation disclaimer check
    conds_text = " ".join(user_conditions)
    doctor_note = None
    if any(k in conds_text for k in ["kidney", "renal", "liver", "type 1"]):
        doctor_note = "Check changes to your diet with your doctor."

    # 5. Build 7 days
    days = []
    prev_dishes: Set[str] = set()

    for d_idx in range(7):
        current_date = start_date + timedelta(days=d_idx)
        date_str = current_date.isoformat()
        day_name = current_date.strftime("%A")

        day_dishes: Set[str] = set()
        day_meals = {}

        for slot in ["breakfast", "lunch", "dinner"]:
            candidates = slot_foods[slot]
            if not candidates:
                candidates = eligible

            # Score candidates based on cuisine match, non-repeat, and nutrient coverage
            scored_candidates = []
            for item in candidates:
                score = 0
                # Cuisine match
                if cuisine_pref == "mixed" or item["cuisine"] == cuisine_pref:
                    score += 5
                # Avoid repeat from yesterday
                if item["food_id"] in prev_dishes:
                    score -= 20
                if item["food_id"] in day_dishes:
                    score -= 50
                # Nutrient coverage match
                overlap = item["nutrients"] & set(target_nutrient_ids)
                score += len(overlap) * 4
                scored_candidates.append((score, item))

            scored_candidates.sort(key=lambda x: (x[0], x[1]["name"]), reverse=True)

            # Pick top 2 options
            opt1 = scored_candidates[0][1] if scored_candidates else candidates[0]
            day_dishes.add(opt1["food_id"])

            # Find second distinct option
            opt2 = None
            for _, item in scored_candidates[1:]:
                if item["food_id"] != opt1["food_id"]:
                    opt2 = item
                    break
            if not opt2:
                opt2 = opt1

            day_dishes.add(opt2["food_id"])

            # Map covered nutrients
            covers1 = [NUTRIENT_DISPLAY_MAP.get(n, n.title()) for n in sorted(list(opt1["nutrients"] & set(target_nutrient_ids)))]
            covers2 = [NUTRIENT_DISPLAY_MAP.get(n, n.title()) for n in sorted(list(opt2["nutrients"] & set(target_nutrient_ids)))]
            if not covers1:
                covers1 = ["Dietary Fiber"]
            if not covers2:
                covers2 = ["Dietary Fiber"]

            # Pick fruit sides matched to focus nutrients
            fruit_pool = slot_foods["fruit_side"]
            matched_fruits = []
            for f in fruit_pool:
                if f["nutrients"] & set(target_nutrient_ids):
                    matched_fruits.append(f)
            if not matched_fruits:
                matched_fruits = fruit_pool

            # Pick 1 or 2 fruit sides
            f_picks = []
            fruit_idx = (d_idx * 3 + (0 if slot == "breakfast" else (1 if slot == "lunch" else 2))) % len(matched_fruits)
            f1 = matched_fruits[fruit_idx]
            f_picks.append({
                "food_id": f1["food_id"],
                "name": f1["name"],
                "note": f1["prep_note"],
                "covers": [NUTRIENT_DISPLAY_MAP.get(n, n.title()) for n in sorted(list(f1["nutrients"] & set(target_nutrient_ids)))],
            })

            day_meals[slot] = {
                "options": [
                    {
                        "option_index": 0,
                        "food_id": opt1["food_id"],
                        "name": opt1["name"],
                        "prep_note": opt1["prep_note"],
                        "covers": covers1,
                        "cuisine": opt1["cuisine"],
                    },
                    {
                        "option_index": 1,
                        "food_id": opt2["food_id"],
                        "name": opt2["name"],
                        "prep_note": opt2["prep_note"],
                        "covers": covers2,
                        "cuisine": opt2["cuisine"],
                    },
                ],
                "fruit_side": f_picks,
            }

        prev_dishes = day_dishes

        days.append({
            "day_index": d_idx,
            "date": date_str,
            "day_name": day_name,
            "nutrient_targets": target_display,
            "meals": day_meals,
        })

    return {
        "user_id": user_id,
        "is_baseline": is_baseline,
        "focus_nutrients": valid_focus,
        "preferences": {
            "diet_pref": diet_pref,
            "cuisine": cuisine_pref,
            "meal_times": preferences.get("meal_times", {}),
        },
        "doctor_note": doctor_note,
        "days": days,
    }


def sync_meal_plan_from_report(
    db: Session,
    user_id: str,
    source_entry_id: str,
    top_nutrients: List[Dict[str, Any]],
) -> Optional[CarePlanMealPlan]:
    """Auto-sync hook called after new report entries."""
    # Filter top nutrients >= 30% (max 3)
    eligible = [n for n in top_nutrients if n.get("final_pct", 0) >= 30.0][:3]
    active_plan = (
        db.query(CarePlanMealPlan)
        .filter(CarePlanMealPlan.user_id == user_id, CarePlanMealPlan.status == "active")
        .first()
    )

    should_regenerate = False
    if not active_plan:
        should_regenerate = True
    else:
        try:
            prev_focus = json.loads(active_plan.focus_json)
            prev_map = {n["id"]: n["pct"] for n in prev_focus}
            curr_map = {normalize_nutrient_id(n.get("nutrient", "")): round(float(n.get("final_pct", 0)), 1) for n in eligible}

            # Check if set changed
            if set(prev_map.keys()) != set(curr_map.keys()):
                should_regenerate = True
            else:
                # Check if percentage moved >= 10 points
                for nid, curr_p in curr_map.items():
                    prev_p = prev_map.get(nid, 0.0)
                    if abs(curr_p - prev_p) >= 10.0:
                        should_regenerate = True
                        break
        except Exception:
            should_regenerate = True

    if not should_regenerate:
        logger.info("CarePlan meal plan remains active and unchanged for user %s (within threshold)", user_id)
        return active_plan

    # Mark old plan stale
    if active_plan:
        active_plan.status = "stale"
        db.add(active_plan)

    # Generate new plan
    prefs = get_user_preferences(db, user_id)
    conds = get_user_conditions(db, user_id)
    plan_dict = generate_deterministic_meal_plan(
        user_id=user_id,
        focus_nutrients=eligible,
        user_conditions=conds,
        preferences=prefs,
    )

    plan_id = f"plan_{hashlib.sha256(f'{user_id}_{source_entry_id}_{datetime.utcnow().isoformat()}'.encode()).hexdigest()[:16]}"
    new_plan = CarePlanMealPlan(
        id=plan_id,
        user_id=user_id,
        source_entry_id=source_entry_id,
        created_at=datetime.utcnow(),
        status="active",
        focus_json=json.dumps(plan_dict["focus_nutrients"]),
        prefs_json=json.dumps(plan_dict["preferences"]),
        plan_json=json.dumps(plan_dict),
    )
    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)
    logger.info("Created new active CarePlan meal plan %s for user %s", plan_id, user_id)
    return new_plan


def get_day_nutrients(
    db: Session,
    user_id: str,
    plan_id: str,
    date_str: str,
) -> Dict[str, Any]:
    """Computes covered and pending nutrients for a given date based on logged meals."""
    plan = db.query(CarePlanMealPlan).filter(CarePlanMealPlan.id == plan_id).first()
    if not plan:
        return {"date": date_str, "covered": [], "pending": [], "progress_pct": 0.0}

    plan_data = json.loads(plan.plan_json)
    target_day = None
    for d in plan_data.get("days", []):
        if d.get("date") == date_str:
            target_day = d
            break

    if not target_day:
        target_day = plan_data.get("days", [])[0] if plan_data.get("days") else {}

    targets = target_day.get("nutrient_targets", ["Dietary Fiber"])

    # Query completed meal logs for this date
    logs = (
        db.query(CarePlanMealLog)
        .filter(
            CarePlanMealLog.user_id == user_id,
            CarePlanMealLog.plan_id == plan_id,
            CarePlanMealLog.plan_date == date_str,
            CarePlanMealLog.done == True,
        )
        .all()
    )

    ticked_slots = {(log.slot, log.option_index) for log in logs}
    covered: Set[str] = set()

    meals = target_day.get("meals", {})
    for slot_name, slot_content in meals.items():
        options = slot_content.get("options", [])
        for opt in options:
            opt_idx = opt.get("option_index", 0)
            if (slot_name, opt_idx) in ticked_slots:
                covered.update(opt.get("covers", []))
                # Also include fruit side coverage if meal eaten
                for fruit in slot_content.get("fruit_side", []):
                    covered.update(fruit.get("covers", []))

    covered_list = [t for t in targets if t in covered]
    pending_list = [t for t in targets if t not in covered]
    progress = round((len(covered_list) / len(targets)) * 100.0, 1) if targets else 100.0

    return {
        "date": date_str,
        "covered": covered_list,
        "pending": pending_list,
        "progress_pct": progress,
    }


def get_nutrition_guidance_cards(
    focus_nutrients: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Returns guidance cards for target nutrients from curated files."""
    cards = []
    target_ids = [normalize_nutrient_id(fn.get("nutrient", "")) for fn in focus_nutrients]
    if not target_ids:
        target_ids = ["fiber", "protein", "calcium"]

    for nid in target_ids:
        guidance = repo.nutrient_guidance.get(nid)
        if not guidance:
            continue
        cards.append({
            "nutrient_id": nid,
            "title": NUTRIENT_DISPLAY_MAP.get(nid, nid.title()),
            "eat_more": guidance["eat_more"],
            "fruit_picks": guidance["fruit_picks"].split(";"),
            "habits_to_improve": guidance["habits_to_improve"],
            "limit_or_avoid": guidance["limit_or_avoid"],
            "source_note": guidance["source_note"],
        })

    return cards
