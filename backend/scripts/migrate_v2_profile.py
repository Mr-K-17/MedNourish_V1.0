"""Idempotent database migration script for MedNourish v2 User Profile columns.

Adds C-33 columns:
- age (INT, nullable)
- blood_type (VARCHAR(10), nullable)
- conditions_json (VARCHAR(2048), nullable)
- other_condition (VARCHAR(100), nullable)

Works idempotently across:
- Local SQLite (mednourish_dev.db)
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

COLUMNS_TO_ADD = [
    ("age", "INTEGER", "INT NULL"),
    ("blood_type", "VARCHAR(10)", "VARCHAR(10) NULL"),
    ("conditions_json", "VARCHAR(2048)", "VARCHAR(2048) NULL"),
    ("other_condition", "VARCHAR(100)", "VARCHAR(100) NULL"),
]


def migrate_engine(engine, db_label: str) -> bool:
    """Migrates a specific engine target idempotently."""
    logger.info("Checking migration on target: %s", db_label)
    try:
        # Create tables if not present
        Base.metadata.create_all(bind=engine)

        inspector = inspect(engine)
        if not inspector.has_table("user_profiles"):
            logger.info("Created user_profiles table on %s", db_label)
            return True

        existing_cols = {col["name"] for col in inspector.get_columns("user_profiles")}
        is_sqlite = "sqlite" in engine.url.drivername

        with engine.begin() as conn:
            for col_name, sqlite_type, mysql_type in COLUMNS_TO_ADD:
                if col_name not in existing_cols:
                    col_type = sqlite_type if is_sqlite else mysql_type
                    sql = f"ALTER TABLE user_profiles ADD COLUMN {col_name} {col_type}"
                    logger.info("Executing on %s: %s", db_label, sql)
                    conn.execute(text(sql))
                    existing_cols.add(col_name)
                else:
                    logger.info("Column '%s' already exists on %s (skipping)", col_name, db_label)
        logger.info("Migration successful on %s", db_label)
        return True
    except Exception as exc:
        logger.warning("Migration failed/skipped on %s: %s", db_label, exc)
        return False


def main():
    logger.info("Starting MedNourish v2 Profile schema migration...")
    
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

    logger.info("Profile schema migration finished.")


if __name__ == "__main__":
    main()
