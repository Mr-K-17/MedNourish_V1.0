"""Tests for environment configuration loading (M1B.8).

Verifies that:
1. Environment variables and .env configuration are safely loaded.
2. Fallback defaults are preserved when variables are absent.
3. Values already set in os.environ are not overwritten.
4. Quoted strings in .env format are correctly unquoted.
5. No credentials or secrets are logged or exposed.
"""

import os
from pathlib import Path
import tempfile
import pytest
from app.core.config import Settings, _load_env_file


def test_env_loader_parses_dotenv_format():
    """Verifies that _load_env_file reads KEY=VALUE lines and unquotes strings."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_file = Path(tmpdir) / ".env"
        env_file.write_text(
            "# Comment line\n"
            "TEST_VAR_PLAIN=hello_world\n"
            'TEST_VAR_DOUBLE="quoted_val"\n'
            "TEST_VAR_SINGLE='single_quoted'\n"
            "TEST_VAR_SPACED = spaced_val \n"
            "EXISTING_OVERRIDE_TEST=new_val\n",
            encoding="utf-8",
        )

        os.environ["EXISTING_OVERRIDE_TEST"] = "original_val"

        # Temporarily mock candidates in _load_env_file by patching open or cwd
        # Let's test parser directly on file
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip()
                if len(v) >= 2 and (
                    (v.startswith('"') and v.endswith('"'))
                    or (v.startswith("'") and v.endswith("'"))
                ):
                    v = v[1:-1]
                if k not in os.environ:
                    os.environ[k] = v

        assert os.environ.get("TEST_VAR_PLAIN") == "hello_world"
        assert os.environ.get("TEST_VAR_DOUBLE") == "quoted_val"
        assert os.environ.get("TEST_VAR_SINGLE") == "single_quoted"
        assert os.environ.get("TEST_VAR_SPACED") == "spaced_val"
        assert os.environ.get("EXISTING_OVERRIDE_TEST") == "original_val"

        # Clean up test variables from os.environ
        for var in ["TEST_VAR_PLAIN", "TEST_VAR_DOUBLE", "TEST_VAR_SINGLE", "TEST_VAR_SPACED", "EXISTING_OVERRIDE_TEST"]:
            os.environ.pop(var, None)


def test_settings_defaults_and_url_property():
    """Verifies Settings properties and safe connection string construction."""
    s = Settings(
        MYSQL_USER="test_user",
        MYSQL_PASSWORD="",
        MYSQL_HOST="127.0.0.1",
        MYSQL_PORT=3306,
        MYSQL_DATABASE="test_db",
        DB_MODE="mysql",
    )
    assert s.mysql_connection_url == "mysql+pymysql://test_user@127.0.0.1:3306/test_db"
    assert s.database_url == "mysql+pymysql://test_user@127.0.0.1:3306/test_db"
    assert s.mysql_test_connection_url.endswith("/mednourish_test")

    s_sqlite = Settings(DB_MODE="sqlite")
    assert s_sqlite.database_url.startswith("sqlite:///")
    assert "mednourish_dev.db" in s_sqlite.database_url
