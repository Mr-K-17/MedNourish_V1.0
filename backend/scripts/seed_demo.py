"""MedNourish — Seed Demo Database Script
==========================================
Module: backend.scripts.seed_demo
Spec: Phase 3.3 Stage 7

Generates reproducible fictional demo records in local SQLite (or configured DB)
for academic/developer demonstrations:
- Fictional adult profile (18+ confirmed, educational consent v1.0).
- Fictional wellness tasks (hydration, brisk walk, sleep hygiene - zero medication).
- Fictional reference-table match summary records (Explorer & MedBot).
- Clean teardown and deterministic repopulation.

Adheres strictly to:
- PRD PROF-01: No DOB or age fields; minimal demographics only.
- CARE-02: Zero medication, drug, or supplement routines.
- REPORT-01: Reference-table match records only; zero clinical risk scores/probabilities.
- Fictional data only (C-24).
"""

from datetime import datetime
import json
import logging
import os
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend root is on path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import settings
from app.db.session import Base
from app.models.user import (
    UserProfile,
    UserConsentLog,
    SavedSummary,
    CarePlanItem,
    MedScanSession,
    CarePlanPrefs,
    CarePlanMealPlan,
    CarePlanMealLog,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("seed_demo")

DEMO_USER_ID = "demo-user-academic-001"


def seed_database(db_url: str = None) -> None:
    if db_url is None:
        db_url = settings.database_url
    logger.info("Initializing database connection (mode=%s)...", settings.DB_MODE)
    engine = create_engine(db_url, connect_args={"check_same_thread": False} if "sqlite" in db_url else {})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # 1. Clean existing demo user records
        db.query(CarePlanMealLog).filter(CarePlanMealLog.user_id == DEMO_USER_ID).delete()
        db.query(CarePlanMealPlan).filter(CarePlanMealPlan.user_id == DEMO_USER_ID).delete()
        db.query(CarePlanPrefs).filter(CarePlanPrefs.user_id == DEMO_USER_ID).delete()
        db.query(MedScanSession).filter(MedScanSession.user_id == DEMO_USER_ID).delete()
        db.query(CarePlanItem).filter(CarePlanItem.user_id == DEMO_USER_ID).delete()
        db.query(SavedSummary).filter(SavedSummary.user_id == DEMO_USER_ID).delete()
        db.query(UserConsentLog).filter(UserConsentLog.user_id == DEMO_USER_ID).delete()
        db.query(UserProfile).filter(UserProfile.id == DEMO_USER_ID).delete()
        db.commit()

        # 2. Seed Fictional User Profile
        profile = UserProfile(
            id=DEMO_USER_ID,
            display_name="Dr. Alex Rivera (Fictional Demo)",
            gender="Non-binary",
            height_cm=175.0,
            weight_kg=68.5,
            age=34,
            blood_type="O+",
            conditions_json=json.dumps(["Anemia"]),
            other_condition=None,
            is_adult_confirmed=True,
            terms_consent_version="v1.0",
            consent_timestamp=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(profile)

        # 3. Seed Consent Audit Log
        consent_log = UserConsentLog(
            user_id=DEMO_USER_ID,
            event_type="CONSENT_GRANTED",
            consent_version="v1.0",
            timestamp=datetime.utcnow(),
        )
        db.add(consent_log)

        # 4. Seed Fictional CarePlan Wellness Tasks (Strictly Non-Medication)
        tasks = [
            CarePlanItem(
                id="task-demo-01",
                user_id=DEMO_USER_ID,
                title="Drink 2 Litres of water throughout the day",
                category="water",
                target_frequency="daily",
                reminder_time="09:00",
                is_completed=True,
                completed_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
            ),
            CarePlanItem(
                id="task-demo-02",
                user_id=DEMO_USER_ID,
                title="30-minute afternoon outdoor brisk walking",
                category="exercise",
                target_frequency="daily",
                reminder_time="17:00",
                is_completed=False,
                completed_at=None,
                created_at=datetime.utcnow(),
            ),
            CarePlanItem(
                id="task-demo-03",
                user_id=DEMO_USER_ID,
                title="Prepare leafy greens and mixed citrus salad",
                category="food",
                target_frequency="daily",
                reminder_time="19:30",
                is_completed=False,
                completed_at=None,
                created_at=datetime.utcnow(),
            ),
            CarePlanItem(
                id="task-demo-04",
                user_id=DEMO_USER_ID,
                title="Screen-off routine 45 minutes before sleep",
                category="sleep",
                target_frequency="daily",
                reminder_time="22:30",
                is_completed=True,
                completed_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
            ),
        ]
        for t in tasks:
            db.add(t)

        # 5. Seed Fictional Multi-Region Reference Match Summaries
        matched_sample_nails = [
            {
                "class_label": "Koilonychia_Spoon_Nails",
                "body_region": "Nails",
                "category": "Mineral Reference Association",
                "vitamin_deficiency_association": "Iron (Informational Reference)",
                "matched_tags": ["spoon_shaped_nails", "brittle_ridges"],
                "match_count": 2,
                "total_condition_tags": 3,
                "review_status": "unreviewed draft",
            },
            {
                "class_label": "Pale_Nail_Beds",
                "body_region": "Nails",
                "category": "Nutritional Reference Association",
                "vitamin_deficiency_association": "Iron / Folate (Informational Reference)",
                "matched_tags": ["spoon_shaped_nails"],
                "match_count": 1,
                "total_condition_tags": 2,
                "review_status": "unreviewed draft",
            },
        ]

        summary_nails = SavedSummary(
            id="summary-demo-nails-01",
            user_id=DEMO_USER_ID,
            session_type="Explorer",
            body_region_filter="Nails",
            selected_tags_json=json.dumps(["spoon_shaped_nails", "brittle_ridges"]),
            matched_entries_json=json.dumps(matched_sample_nails),
            match_count_total=2,
            package_version="kb-curated-v1.0",
            matcher_version="matcher-rule-v1.0",
            review_status="unreviewed draft",
            disclaimer="Educational prototype reference summary only. Not a medical diagnosis or clinical prescription.",
            created_at=datetime.utcnow(),
        )
        db.add(summary_nails)

        matched_sample_eyes = [
            {
                "class_label": "Bitot_Spots",
                "body_region": "Eyes",
                "category": "Vitamin Reference Association",
                "vitamin_deficiency_association": "Vitamin A (Informational Reference)",
                "matched_tags": ["nightblindness", "eyedryness"],
                "match_count": 2,
                "total_condition_tags": 4,
                "review_status": "unreviewed draft",
            },
            {
                "class_label": "Conjunctival_Xerosis",
                "body_region": "Eyes",
                "category": "Vitamin Reference Association",
                "vitamin_deficiency_association": "Vitamin A (Informational Reference)",
                "matched_tags": ["eyedryness"],
                "match_count": 1,
                "total_condition_tags": 3,
                "review_status": "unreviewed draft",
            },
        ]

        summary_eyes = SavedSummary(
            id="summary-demo-eyes-02",
            user_id=DEMO_USER_ID,
            session_type="MedBot",
            body_region_filter="Eyes",
            selected_tags_json=json.dumps(["nightblindness", "eyedryness"]),
            matched_entries_json=json.dumps(matched_sample_eyes),
            match_count_total=2,
            package_version="kb-curated-v1.0",
            matcher_version="matcher-rule-v1.0",
            review_status="unreviewed draft",
            disclaimer="Educational prototype reference summary only. Not a medical diagnosis or clinical prescription.",
            created_at=datetime.utcnow(),
        )
        db.add(summary_eyes)

        matched_sample_tongue = [
            {
                "class_label": "Atrophic_Glossitis",
                "body_region": "Tongue",
                "category": "B-Complex Reference Association",
                "vitamin_deficiency_association": "Vitamin B12 / Folate (Informational Reference)",
                "matched_tags": ["smooth_red_tongue", "burning_sensation"],
                "match_count": 2,
                "total_condition_tags": 3,
                "review_status": "unreviewed draft",
            }
        ]

        summary_tongue = SavedSummary(
            id="summary-demo-tongue-03",
            user_id=DEMO_USER_ID,
            session_type="Explorer",
            body_region_filter="Tongue",
            selected_tags_json=json.dumps(["smooth_red_tongue", "burning_sensation"]),
            matched_entries_json=json.dumps(matched_sample_tongue),
            match_count_total=1,
            package_version="kb-curated-v1.0",
            matcher_version="matcher-rule-v1.0",
            review_status="unreviewed draft",
            disclaimer="Educational prototype reference summary only. Not a medical diagnosis or clinical prescription.",
            created_at=datetime.utcnow(),
        )
        db.add(summary_tongue)

        # 6. Seed Fictional MedScan-Lite Quality Check Session
        medscan_metrics = {
            "resolution": "1080x1080",
            "laplacian_variance": 348.2,
            "mean_luminance": 124.5,
            "blur_check": "PASS",
            "lighting_check": "PASS",
            "file_size_bytes": 142050,
        }
        medscan_session = MedScanSession(
            id="medscan-demo-01",
            user_id=DEMO_USER_ID,
            body_region="Tongue",
            image_count=1,
            quality_status="PASSED",
            quality_metrics_json=json.dumps(medscan_metrics),
            notes="Routine monthly reference lighting check (fictional demonstration).",
            created_at=datetime.utcnow(),
        )
        db.add(medscan_session)

        # 6. Seed Fictional CarePlan Meal Preferences & Plan (C-39)
        from app.services.meal_plan_service import generate_deterministic_meal_plan
        demo_prefs = CarePlanPrefs(
            user_id=DEMO_USER_ID,
            diet_pref="veg",
            cuisine="indian",
            meal_times_json=json.dumps({"breakfast": "08:30", "lunch": "13:00", "dinner": "20:00"}),
            updated_at=datetime.utcnow(),
        )
        db.add(demo_prefs)

        demo_focus = [
            {"nutrient": "Iron", "percentage": 68.0, "source": "MedBot"},
            {"nutrient": "Vitamin A", "percentage": 42.0, "source": "Explorer"},
        ]
        demo_plan_dict = generate_deterministic_meal_plan(
            user_id=DEMO_USER_ID,
            focus_nutrients=demo_focus,
            user_conditions=["anemia"],
            preferences={"diet_pref": "veg", "cuisine": "indian", "meal_times": {"breakfast": "08:30", "lunch": "13:00", "dinner": "20:00"}},
        )
        demo_meal_plan = CarePlanMealPlan(
            id="plan-demo-user-01",
            user_id=DEMO_USER_ID,
            source_entry_id="sum-medbot-01",
            created_at=datetime.utcnow(),
            status="active",
            focus_json=json.dumps(demo_plan_dict["focus_nutrients"]),
            prefs_json=json.dumps(demo_plan_dict["preferences"]),
            plan_json=json.dumps(demo_plan_dict),
        )
        db.add(demo_meal_plan)

        db.commit()
        logger.info("Successfully seeded fictional demo records for user '%s'.", DEMO_USER_ID)
        logger.info("Created: 1 profile, 1 consent log, 4 wellness tasks, 3 saved summaries, 1 MedScan session.")

    except Exception as e:
        db.rollback()
        logger.error("Failed to seed demo database: %s", str(e))
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
