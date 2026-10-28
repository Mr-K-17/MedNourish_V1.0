"""Idempotent database migration script for MedNourish Phase 5 Reports & CarePlan columns.

Adds:
1. saved_summaries:
   - snapshot_scores_json (VARCHAR(4096), nullable)
2. care_plan_items:
   - is_auto (BOOLEAN / TINYINT(1) DEFAULT 0 NOT NULL)
   - source_entry_id (VARCHAR(64), nullable)
   - nutrient (VARCHAR(64), nullable)
   - text_hash (VARCHAR(64), nullable)
   - is_stale (BOOLEAN / TINYINT(1) DEFAULT 0 NOT NULL)
   - is_user_edited (BOOLEAN / TINYINT(1) DEFAULT 0 NOT NULL)

Works idempotently across:
- SQLite (mednourish_dev.db)
- MySQL mednourish_dev
- MySQL mednourish_test
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

MIGRATIONS = [
    {
        "table": "saved_summaries",
        "columns": [
            ("snapshot_scores_json", "VARCHAR(4096)", "VARCHAR(4096) NULL"),
        ],
    },
    {
        "table": "care_plan_items",
        "columns": [
            ("is_auto", "BOOLEAN DEFAULT 0 NOT NULL", "TINYINT(1) DEFAULT 0 NOT NULL"),
            ("source_entry_id", "VARCHAR(64)", "VARCHAR(64) NULL"),
            ("nutrient", "VARCHAR(64)", "VARCHAR(64) NULL"),
            ("text_hash", "VARCHAR(64)", "VARCHAR(64) NULL"),
            ("is_stale", "BOOLEAN DEFAULT 0 NOT NULL", "TINYINT(1) DEFAULT 0 NOT NULL"),
            ("is_user_edited", "BOOLEAN DEFAULT 0 NOT NULL", "TINYINT(1) DEFAULT 0 NOT NULL"),
        ],
    },
]


def migrate_engine(engine, db_label: str) -> bool:
    """Migrates a specific engine target idempotently."""
    logger.info("Checking migration on target: %s", db_label)
    try:
        # Create any missing tables
        Base.metadata.create_all(bind=engine)

        inspector = inspect(engine)
        is_sqlite = "sqlite" in engine.url.drivername

        with engine.begin() as conn:
            for item in MIGRATIONS:
                table_name = item["table"]
                if not inspector.has_table(table_name):
                    continue

                existing_cols = {col["name"] for col in inspector.get_columns(table_name)}
                for col_name, sqlite_type, mysql_type in item["columns"]:
                    if col_name not in existing_cols:
                        col_type = sqlite_type if is_sqlite else mysql_type
                        sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}"
                        logger.info("Executing on %s (%s): %s", db_label, table_name, sql)
                        conn.execute(text(sql))
                        existing_cols.add(col_name)
                    else:
                        logger.info("Column '%s.%s' already exists on %s", table_name, col_name, db_label)

        logger.info("Migration successful on %s", db_label)
        return True
    except Exception as exc:
        logger.warning("Migration failed/skipped on %s: %s", db_label, exc)
        return False


def main():
    logger.info("Starting MedNourish Phase 5 schema migration...")

    # 1. Migrate SQLite
    sqlite_url = f"sqlite:///{settings.sqlite_file_path.as_posix()}"
    sqlite_engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
    migrate_engine(sqlite_engine, "SQLite (mednourish_dev.db)")

    # 2. Migrate MySQL mednourish_dev
    mysql_dev_url = settings.mysql_connection_url
    try:
        mysql_dev_engine = create_engine(mysql_dev_url, pool_pre_ping=True, connect_args={"connect_timeout": 3})
        migrate_engine(mysql_dev_engine, "MySQL (mednourish_dev)")
    except Exception as exc:
        logger.warning("Could not connect to MySQL mednourish_dev: %s", exc)

    # 3. Migrate MySQL mednourish_test
    mysql_test_url = settings.mysql_test_connection_url
    try:
        mysql_test_engine = create_engine(mysql_test_url, pool_pre_ping=True, connect_args={"connect_timeout": 3})
        migrate_engine(mysql_test_engine, "MySQL (mednourish_test)")
    except Exception as exc:
        logger.warning("Could not connect to MySQL mednourish_test: %s", exc)

    logger.info("Phase 5 schema migration finished.")


if __name__ == "__main__":
    main()
