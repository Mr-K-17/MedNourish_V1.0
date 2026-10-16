"""Idempotent database migration script for MedNourish Phase 5 / CarePlan v3 meal planning.

Creates tables idempotently:
1. careplan_prefs:
   - user_id (VARCHAR(128) PRIMARY KEY)
   - diet_pref (VARCHAR(32) NOT NULL DEFAULT 'veg')
   - cuisine (VARCHAR(32) NOT NULL DEFAULT 'indian')
   - meal_times_json (VARCHAR(512) NOT NULL DEFAULT '{"breakfast":"08:00","lunch":"13:00","dinner":"20:00"}')
   - updated_at (DATETIME NOT NULL)
2. careplan_meal_plan:
   - id (VARCHAR(64) PRIMARY KEY)
   - user_id (VARCHAR(128) NOT NULL INDEX)
   - source_entry_id (VARCHAR(64) NULL)
   - created_at (DATETIME NOT NULL)
   - status (VARCHAR(32) NOT NULL DEFAULT 'active')
   - focus_json (TEXT NOT NULL)
   - prefs_json (TEXT NOT NULL)
   - plan_json (TEXT NOT NULL)
3. careplan_meal_log:
   - id (VARCHAR(64) PRIMARY KEY)
   - user_id (VARCHAR(128) NOT NULL INDEX)
   - plan_id (VARCHAR(64) NOT NULL INDEX)
   - plan_date (VARCHAR(16) NOT NULL)
   - slot (VARCHAR(32) NOT NULL)
   - option_index (INT NOT NULL DEFAULT 0)
   - done (BOOLEAN / TINYINT(1) NOT NULL DEFAULT 0)
   - done_at (DATETIME NULL)

Tested on SQLite and MySQL (mednourish_dev, mednourish_test).
Never drops tables, never truncates data.
"""

import sys
import logging
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine, inspect, text
from app.core.config import settings
from app.db.session import Base
import app.models.user  # ensure models are registered with Base.metadata

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def migrate_engine(engine, db_label: str) -> bool:
    """Migrates a specific engine target idempotently."""
    logger.info("Checking CarePlan v3 migration on target: %s", db_label)
    try:
        # Create all registered tables if they do not exist
        Base.metadata.create_all(bind=engine)
        inspector = inspect(engine)

        required_tables = ["careplan_prefs", "careplan_meal_plan", "careplan_meal_log"]
        for tbl in required_tables:
            if not inspector.has_table(tbl):
                logger.error("Table '%s' was not created on %s", tbl, db_label)
                return False
            logger.info("Table '%s' verified on %s", tbl, db_label)

        logger.info("CarePlan v3 migration successfully applied and verified on %s", db_label)
        return True
    except Exception as exc:
        logger.warning("Migration failed on %s: %s", db_label, exc)
        return False


def run_all_migrations():
    """Runs migration across SQLite and MySQL instances."""
    results = {}

    # 1. SQLite default / local dev DB
    sqlite_url = f"sqlite:///{Path(__file__).resolve().parents[1]}/mednourish_dev.db"
    sqlite_engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
    results["SQLite (mednourish_dev.db)"] = migrate_engine(sqlite_engine, "SQLite mednourish_dev.db")

    # 2. Configured database from settings
    configured_engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
    )
    results[f"Configured DB ({settings.DB_MODE})"] = migrate_engine(configured_engine, f"Configured DB ({settings.DB_MODE})")

    # 3. MySQL mednourish_dev and mednourish_test if accessible
    mysql_bases = [
        ("MySQL mednourish_dev", f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/mednourish_dev"),
        ("MySQL mednourish_test", f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/mednourish_test"),
    ]

    for label, url in mysql_bases:
        try:
            my_eng = create_engine(url, connect_args={"connect_timeout": 3})
            results[label] = migrate_engine(my_eng, label)
        except Exception as e:
            logger.info("Skipping %s (server unreachable or not configured): %s", label, e)
            results[label] = "skipped (unreachable)"

    logger.info("=== CarePlan v3 Migration Summary ===")
    for target, res in results.items():
        logger.info("  %s: %s", target, res)
    return results


if __name__ == "__main__":
    run_all_migrations()
