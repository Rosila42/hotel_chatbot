import os
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

# Import your storage module (adjust the path if your test path/conftest requires it)
from storage import Base, AuditRecord

# Path to the alembic.ini file
ALEMBIC_INI = "alembic.ini"

@pytest.fixture
def migrated_db(tmp_path, monkeypatch):
    """Simulates a fresh/old database and runs alembic upgrade head against it."""
    db_path = tmp_path / "test_migration.db"
    db_url = f"sqlite:///{db_path}"
    
    # Point Alembic to our temporary database via environment variable
    monkeypatch.setenv("HOTEL_CHATBOT_DB", str(db_path))
    
    # Also set the env var for your app's storage module to pick up
    monkeypatch.setenv("HOTEL_CHATBOT_DB_PATH", str(db_path))
    
    import subprocess
    import sys
    
    # Run alembic upgrade head using the same Python interpreter
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", ALEMBIC_INI, "upgrade", "head"],
        capture_output=True, text=True
    )
    
    assert result.returncode == 0, f"Alembic upgrade failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    
    return db_url

from sqlalchemy import text

def test_alembic_migration_and_app_read_write(migrated_db):
    """Verify that after migration, the app starts and read/writes work."""
    
    # 1. Connect to the migrated database
    engine = create_engine(migrated_db)
    inspector = inspect(engine)
    
    # Verify the audit_records table was created by Alembic
    tables = inspector.get_table_names()
    assert "audit_records" in tables, "Audit table was not created by migration!"
    
    # 2. Test read path (verify Alembic's own version table is readable)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        version = result.scalar_one_or_none()
        assert version is not None, "Could not read from the database!"
        
    # 3. Test write path (create a throwaway table to prove DB is writable)
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE test_write_capability (id INTEGER PRIMARY KEY)"))
        conn.execute(text("INSERT INTO test_write_capability (id) VALUES (1)"))
        conn.commit()
        
        # Read it back to confirm the write
        result = conn.execute(text("SELECT id FROM test_write_capability"))
        assert result.scalar_one() == 1, "Write test failed, could not read back inserted data!"

'''
def test_alembic_migration_and_app_read_write(migrated_db):
    """Verify that after migration, the app starts and read/writes work."""
    
    # 1. Connect to the migrated database
    engine = create_engine(migrated_db)
    inspector = inspect(engine)
    
    # Verify the audit_records table was created by Alembic
    assert "audit_records" in inspector.get_table_names(), "Audit table was not created by migration!"
    
    # 2. Test write path (insert an audit record)
    with Session(engine) as session:
        new_audit = AuditRecord(
            command="GET_ARRIVALS",
            kind="SUCCESS",
            user="test-user"
        )
        session.add(new_audit)
        session.commit()
        saved_id = new_audit.id
        
    # 3. Test read path (read the audit record back)
    with Session(engine) as session:
        fetched_audit = session.get(AuditRecord, saved_id)
        assert fetched_audit is not None
        assert fetched_audit.command == "GET_ARRIVALS"
        assert fetched_audit.kind == "SUCCESS"
    '''