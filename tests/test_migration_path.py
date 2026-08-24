from __future__ import annotations

import subprocess
import sys

from sqlalchemy import create_engine, inspect, text


ALEMBIC_INI = "alembic.ini"


def test_alembic_migration_and_app_read_write(tmp_path, monkeypatch):
    """Verify a fresh database can be created and used through Alembic."""
    db_path = tmp_path / "test_migration.db"
    db_url = f"sqlite:///{db_path}"
    monkeypatch.setenv("HOTEL_CHATBOT_DB", str(db_path))

    result = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", ALEMBIC_INI, "upgrade", "head"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"Alembic upgrade failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )

    engine = create_engine(db_url)
    tables = set(inspect(engine).get_table_names())
    assert "audit_records" in tables
    assert "chat_sessions" in tables
    assert "alembic_version" in tables

    with engine.connect() as conn:
        version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        assert version == "b29ad92612b1"

        conn.execute(text("CREATE TABLE test_write_capability (id INTEGER PRIMARY KEY)"))
        conn.execute(text("INSERT INTO test_write_capability (id) VALUES (1)"))
        conn.commit()
        saved = conn.execute(text("SELECT id FROM test_write_capability")).scalar_one()
        assert saved == 1
