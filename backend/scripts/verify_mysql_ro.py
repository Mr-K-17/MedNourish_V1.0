"""Verify local MySQL connectivity read-only using settings from .env without printing secrets."""
import sys
import os

backend_dir = r"C:\Users\USER\Desktop\MedNourish-Dev\backend"
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import settings
from sqlalchemy import create_engine, text

def check_mysql():
    url = settings.mysql_connection_url
    print(f"Connecting to MySQL host: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}, user: {settings.MYSQL_USER}, db: {settings.MYSQL_DATABASE}")
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            res_val = conn.execute(text("SELECT 1")).scalar()
            curr_db = conn.execute(text("SELECT DATABASE()")).scalar()
            print(f"SUCCESS: Read-only query 'SELECT 1' returned: {res_val}")
            print(f"Current active database: {curr_db}")
    except Exception as e:
        print(f"Connection result: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    check_mysql()
