# CarePlan v3 Deterministic Meal Planner Specification (C-39)

## 1. Root Cause of Previous One-Liners
In Version 2, `backend/app/services/careplan_sync_service.py` (`clean_routine_text()`, lines 45–78) aggressively parsed raw CSV routine strings from `*_Vitamin_Deficiency_to_Suggested_Routine.csv`. It stripped punctuation, truncated lines to 135 characters, and created a single task title formatted as `"Nutrition focus: " + text.split(".")[0]`. When CSV entries contained statements like `"Eat mango. Eat citrus fruit. Avoid processed sugar."`, the parser took only the first fragment, yielding overly simplistic one-liners like `"Nutrition focus: Eat mango"`. Decision **C-39** resolves this by replacing raw string parsing with a structured, deterministic 7-day meal planner backed by a curated food catalog.

## 2. Curated Food Knowledge Catalog Statistics
- **Catalog File**: `knowledge/curated/food_items.csv` (206 items, all prep notes <= 60 characters).
- **Nutrient Guidance File**: `knowledge/curated/nutrient_guidance.csv` (18 target nutrients).
- **Cuisines**: Indian (regional staples including chapathi, ragi, jowar, bajra, poha, upma, idli, dal, rajma, sambar, paneer, curd) and Global (oats, salads, grilled fish, fruit bowls).
- **Diet Tags**: `veg`, `vegan`, `egg`, `nonveg`.
- **Allergens**: `gluten`, `dairy`, `nuts`, `egg`, `fish`, `soy`.
- **Cautions / Condition Filters**: `high_sugar` (diabetes filter), `high_sodium` (hypertension filter), `high_potassium` (kidney condition filter).
- **Food Groups**: cereal, millet, pulse, vegetable, leafy_green, fruit, dairy, egg, meat, fish, nut_seed, oil, beverage.

## 3. Deterministic Planner Algorithm
1. **Stable Pseudo-Random Seed**: A SHA-256 hash of `user_id + source_summary_id + day_date` generates integer seeds. Identical inputs yield identical 7-day meal schedules across unlimited iterations.
2. **Filtering Order**:
   - Filter by diet preference (`veg`, `vegan`, `nonveg`, `egg`).
   - Exclude items containing user allergens (`gluten`, `dairy`, `nuts`, `egg`, `fish`, `soy`).
   - Exclude foods with caution flags matching medical conditions (`high_sugar` for diabetes, `high_sodium` for hypertension, `high_potassium` for kidney disease).
3. **Nutrient Coverage & Slots**:
   - Each day fills 3 meal slots (`breakfast`, `lunch`, `dinner`) plus a daily fruit side.
   - Each slot provides **2 distinct options** (`option 0` and `option 1`).
   - Focus nutrients (final probability >= 30%) are guaranteed coverage in >= 2 meals per day.
   - `Dietary Fiber` is scheduled every single day.
4. **Regeneration Threshold**: If repeated assessments yield the same top nutrients or rank order changes by < 10 percentage points, the active plan is preserved to avoid user churn.

## 4. Database Schema & Migration Idempotence
- **Tables Created**:
  - `careplan_prefs`: user diet preferences, cuisine preferences, and custom meal notification times.
  - `careplan_meal_plan`: 7-day active plan JSON, focus nutrients, source entry reference, and lifecycle status (`active` / `stale`).
  - `careplan_meal_log`: daily meal option selection toggles (`done`, `done_at`, `option_index`).
- **Migration Script**: `backend/scripts/migrate_v3_careplan.py` executes idempotent `CREATE TABLE IF NOT EXISTS` and `ADD COLUMN` operations. Verified safe across:
  - SQLite (in-memory and file-based test databases).
  - MySQL `mednourish_dev`.
  - MySQL `mednourish_test`.
- **Account Deletion Cascade**: `backend/app/api/v1/profile.py` cleanly cascades and removes all user meal plans, meal logs, and preferences upon account deletion.

## 5. Disclaimer Contract & Safety Guardrails
- **Mandatory CarePlan Disclaimer**: Exactly `"General food ideas, not a prescribed diet."`
- **Zero Medicalization**: No medicines, no pharmaceutical supplements, no clinical doses (zero `mg`, `mcg`, `IU`), zero calorie counting, and zero gram measurements.
- **Safety Claim Scan**: `backend/scripts/scan_safety_claims.py` audits 76 files and confirms 0 prohibited diagnostic or prescriptive claims.

## 6. Frontend UX & Interactions
- **Daily Navigation**: 7-day tabs (Day 1 through Day 7 / Monday through Sunday).
- **Meal Option Picker**: Radio buttons allow user selection between Option A and Option B, with meal prep notes and covered nutrient tags.
- **Fruit Side**: Dedicated daily fruit recommendation tailored to focus nutrients.
- **Nutrient Tracking Panel**: Real-time progress bar computing `covered` vs `pending` nutrients based on meals ticked as eaten.
- **Nutrition Guidance Accordion**: Expandable cards for focus nutrients showing foods to eat more of, fruit picks, habits to improve, and items to limit or avoid.
- **Calendar Export**: `.ics` export generating standard RFC 5545 `VCALENDAR` feeds for wellness tasks and meal reminders with valid `SUMMARY:MedNourish Meal: ...` entries.

## 7. Verification & Test Suite Summary
- **Determinism**: 10/10 identical runs verified by unit test `test_planner_determinism_x10`.
- **Backend Tests**: **115/115 passed** (10 new dedicated meal planner tests + 6 food knowledge tests + 99 existing tests). Zero regressions.
- **ML Tests**: **40/40 passed** (data pipeline, vision models, tabular models). Zero regressions.
- **TypeScript & Build**: Frontend TypeScript check `npx tsc --noEmit` and Vite production build passed cleanly.
