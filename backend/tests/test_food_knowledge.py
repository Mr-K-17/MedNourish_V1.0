"""Validation tests for MedNourish CarePlan v3 Curated Food Knowledge.

Spec: Step 1 / C-39:
- Schema validation for food_items.csv and nutrient_guidance.csv
- Allowed tags and valid formats
- Banned-term scan (no supplements, doses, mg/mcg/IU, diagnosis, cures)
- Every nutrient in nutrient_guidance appears in >= 8 foods, >= 2 fruits, >= 2 veg/pulse
- Pools for vegan, vegetarian, gluten-free, dairy-free, and non-veg have >= 5 foods for breakfast, lunch, dinner
- All prep_notes <= 60 chars
"""

import csv
import os
import re
import pytest

FOOD_ITEMS_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "knowledge", "curated", "food_items.csv")
)
NUTRIENT_GUIDANCE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "knowledge", "curated", "nutrient_guidance.csv")
)

ALLOWED_CUISINES = {"indian", "global"}
ALLOWED_FOOD_GROUPS = {
    "cereal", "millet", "pulse", "vegetable", "leafy_green",
    "fruit", "dairy", "egg", "meat", "fish", "nut_seed", "oil", "beverage"
}
ALLOWED_MEAL_SLOTS = {"breakfast", "lunch", "dinner", "fruit_side"}
ALLOWED_DIET_TAGS = {"veg", "vegan", "egg", "nonveg"}
ALLOWED_ALLERGENS = {"gluten", "dairy", "nuts", "egg", "fish", "soy"}
ALLOWED_CAUTIONS = {"high_sugar", "high_potassium", "high_sodium"}

BANNED_REGEX = re.compile(
    r"\b(supplement|tablet|capsule|pill|multivitamin|dose|mg|mcg|iu|cure|treat|diagnosis|diagnose|prescribe|prescription)\b",
    re.IGNORECASE
)


@pytest.fixture(scope="module")
def food_items():
    assert os.path.exists(FOOD_ITEMS_PATH), f"File missing: {FOOD_ITEMS_PATH}"
    with open(FOOD_ITEMS_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


@pytest.fixture(scope="module")
def nutrient_guidance():
    assert os.path.exists(NUTRIENT_GUIDANCE_PATH), f"File missing: {NUTRIENT_GUIDANCE_PATH}"
    with open(NUTRIENT_GUIDANCE_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def test_food_items_count(food_items):
    """Ensure at least 150 everyday foods exist."""
    assert len(food_items) >= 150, f"Expected >= 150 foods, got {len(food_items)}"


def test_food_items_schema_and_prep_notes(food_items):
    """Validate column schema, prep note length <= 60 chars, and uniqueness of food_id."""
    expected_cols = {"food_id", "name", "cuisine", "food_group", "meal_slots", "diet_tags", "allergens", "cautions", "nutrients", "prep_note"}
    seen_ids = set()

    for item in food_items:
        assert set(item.keys()) == expected_cols, f"Invalid columns in {item.get('food_id')}"
        fid = item["food_id"]
        assert fid not in seen_ids, f"Duplicate food_id: {fid}"
        seen_ids.add(fid)

        assert item["cuisine"] in ALLOWED_CUISINES, f"Invalid cuisine in {fid}"
        assert item["food_group"] in ALLOWED_FOOD_GROUPS, f"Invalid food_group in {fid}"

        slots = set(item["meal_slots"].split(";"))
        assert slots.issubset(ALLOWED_MEAL_SLOTS), f"Invalid slots in {fid}"

        diets = set(item["diet_tags"].split(";"))
        assert diets.issubset(ALLOWED_DIET_TAGS), f"Invalid diet_tags in {fid}"

        if item["allergens"]:
            allergens = set(item["allergens"].split(";"))
            assert allergens.issubset(ALLOWED_ALLERGENS), f"Invalid allergens in {fid}"

        if item["cautions"]:
            cautions = set(item["cautions"].split(";"))
            assert cautions.issubset(ALLOWED_CAUTIONS), f"Invalid cautions in {fid}"

        assert len(item["prep_note"]) <= 60, f"prep_note > 60 chars in {fid}: {item['prep_note']}"


def test_banned_terms_scan_food_items(food_items):
    """Scan all text fields in food_items.csv for banned pharmaceutical or clinical claim words."""
    for item in food_items:
        for field in ["name", "prep_note"]:
            text = item[field]
            match = BANNED_REGEX.search(text)
            assert not match, f"Prohibited term '{match.group()}' found in {item['food_id']}.{field}: '{text}'"


def test_nutrient_guidance_schema_and_banned_terms(nutrient_guidance):
    """Validate nutrient guidance columns, draft source_note, and absence of banned words."""
    expected_cols = {"nutrient", "eat_more", "fruit_picks", "habits_to_improve", "limit_or_avoid", "source_note"}
    nutrients = set()

    for row in nutrient_guidance:
        assert set(row.keys()) == expected_cols
        assert row["source_note"] == "unreviewed draft"
        nutrients.add(row["nutrient"])

        for field in ["eat_more", "fruit_picks", "habits_to_improve", "limit_or_avoid"]:
            text = row[field]
            match = BANNED_REGEX.search(text)
            assert not match, f"Prohibited term '{match.group()}' in guidance {row['nutrient']}.{field}: '{text}'"

    assert len(nutrients) == 18, f"Expected 18 guidance nutrients, got {len(nutrients)}"


def test_nutrient_coverage_across_food_catalog(food_items, nutrient_guidance):
    """Every nutrient in nutrient_guidance must appear in >= 8 foods, >= 2 fruits, and >= 2 vegetables/pulses."""
    guidance_nutrients = {row["nutrient"] for row in nutrient_guidance}

    nutrient_counts = {n: 0 for n in guidance_nutrients}
    nutrient_fruit_counts = {n: 0 for n in guidance_nutrients}
    nutrient_veg_pulse_counts = {n: 0 for n in guidance_nutrients}

    for item in food_items:
        nutrients = [n.strip() for n in item["nutrients"].split(";") if n.strip()]
        group = item["food_group"]
        slots = item["meal_slots"].split(";")

        for n in nutrients:
            assert n in guidance_nutrients, f"Unknown nutrient '{n}' in food {item['food_id']}"
            nutrient_counts[n] += 1
            if group == "fruit" or "fruit_side" in slots:
                nutrient_fruit_counts[n] += 1
            if group in {"vegetable", "leafy_green", "pulse"}:
                nutrient_veg_pulse_counts[n] += 1

    for n in guidance_nutrients:
        assert nutrient_counts[n] >= 8, f"Nutrient '{n}' appears in only {nutrient_counts[n]} foods (< 8)"
        assert nutrient_fruit_counts[n] >= 2, f"Nutrient '{n}' appears in only {nutrient_fruit_counts[n]} fruits (< 2)"
        assert nutrient_veg_pulse_counts[n] >= 2, f"Nutrient '{n}' appears in only {nutrient_veg_pulse_counts[n]} veg/pulse (< 2)"


def test_diet_and_allergen_pools_coverage(food_items):
    """Vegan, vegetarian, gluten-free, dairy-free, and non-veg pools each have >= 5 options per meal slot."""
    pools = {
        "vegan": {"breakfast": 0, "lunch": 0, "dinner": 0},
        "vegetarian": {"breakfast": 0, "lunch": 0, "dinner": 0},
        "gluten_free": {"breakfast": 0, "lunch": 0, "dinner": 0},
        "dairy_free": {"breakfast": 0, "lunch": 0, "dinner": 0},
        "nonveg": {"breakfast": 0, "lunch": 0, "dinner": 0},
    }

    for item in food_items:
        diets = set(item["diet_tags"].split(";"))
        allergens = set(item["allergens"].split(";")) if item["allergens"] else set()
        slots = set(item["meal_slots"].split(";"))

        is_vegan = ("vegan" in diets)
        is_veg = ("veg" in diets or "vegan" in diets)
        is_gf = ("gluten" not in allergens)
        is_df = ("dairy" not in allergens)
        is_nonveg = ("nonveg" in diets or "egg" in diets)

        for slot in ["breakfast", "lunch", "dinner"]:
            if slot in slots:
                if is_vegan:
                    pools["vegan"][slot] += 1
                if is_veg:
                    pools["vegetarian"][slot] += 1
                if is_gf:
                    pools["gluten_free"][slot] += 1
                if is_df:
                    pools["dairy_free"][slot] += 1
                if is_nonveg:
                    pools["nonveg"][slot] += 1

    for pool_name, slot_counts in pools.items():
        for slot, count in slot_counts.items():
            assert count >= 5, f"Pool '{pool_name}' has only {count} items for slot '{slot}' (< 5)"
