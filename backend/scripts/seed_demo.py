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

from app.db.session import Base
from app.models.user import UserProfile, UserConsentLog, SavedSummary, CarePlanItem

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("seed_demo")

DEMO_USER_ID = "demo-user-academic-001"
SQLITE_DB_PATH = os.path.join(backend_dir, "mednourish_dev.db")
DATABASE_URL = f"sqlite:///{SQLITE_DB_PATH}"


def seed_database(db_url: str = DATABASE_URL) -> None:
    logger.info("Initializing database connection at: %s", db_url)
    engine = create_engine(db_url, connect_args={"check_same_thread": False} if "sqlite" in db_url else {})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # 1. Clean existing demo user records
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

        # 5. Seed Fictional Reference Match Summaries
        matched_sample_1 = [
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

        summary_1 = SavedSummary(
            id="summary-demo-01",
            user_id=DEMO_USER_ID,
            session_type="Explorer",
            body_region_filter="Nails",
            selected_tags_json=json.dumps(["spoon_shaped_nails", "brittle_ridges"]),
            matched_entries_json=json.dumps(matched_sample_1),
            match_count_total=2,
            package_version="kb-curated-v1.0",
            matcher_version="matcher-rule-v1.0",
            review_status="unreviewed draft",
            disclaimer="Educational prototype reference summary only. Not a medical diagnosis or clinical prescription.",
            created_at=datetime.utcnow(),
        )
        db.add(summary_1)

        db.commit()
        logger.info("Successfully seeded fictional demo records for user '%s'.", DEMO_USER_ID)
        logger.info("Created: 1 profile, 1 consent log, 4 wellness tasks, 1 saved summary.")

    except Exception as e:
        db.rollback()
        logger.error("Failed to seed demo database: %s", str(e))
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
