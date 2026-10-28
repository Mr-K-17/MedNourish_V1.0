"""Verify local MySQL server authentication and list available databases."""
import sys
import os

backend_dir = r"C:\Users\USER\Desktop\MedNourish-Dev\backend"
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import settings
from sqlalchemy import create_engine, text

def check_mysql_auth():
    pwd = f":{settings.MYSQL_PASSWORD}" if settings.MYSQL_PASSWORD else ""
    server_url = f"mysql+pymysql://{settings.MYSQL_USER}{pwd}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/"
    print(f"Authenticating to MySQL server at: {settings.MYSQL_HOST}:{settings.MYSQL_PORT} as user '{settings.MYSQL_USER}'...")
    try:
        engine = create_engine(server_url)
        with engine.connect() as conn:
            one = conn.execute(text("SELECT 1")).scalar()
            print(f"SUCCESS: Server authentication passed. 'SELECT 1' returned: {one}")
            dbs = [row[0] for row in conn.execute(text("SHOW DATABASES;"))]
            print(f"Databases present on server: {dbs}")
    except Exception as e:
        print(f"Authentication/query error: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    check_mysql_auth()
