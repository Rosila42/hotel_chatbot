from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Generator

from sqlalchemy import Boolean, DateTime, String, Text, create_engine, event, inspect
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


APP_DATA_DIR = Path(
    os.environ.get(
        "XDG_DATA_HOME",
        str(Path.home() / ".local" / "share"),
    )
) / "hotel-chatbot-v2"
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)


def _database_path() -> Path:
    """Return the canonical runtime database path used by app and migrations."""
    explicit_path = os.environ.get("HOTEL_CHATBOT_DB") or os.environ.get("HOTEL_CHATBOT_TEST_DB")
    return Path(explicit_path) if explicit_path else APP_DATA_DIR / "hotel_chatbot_v2.db"


DATABASE_PATH = _database_path()
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def _configure_sqlite(dbapi_connection, connection_record) -> None:
    """Harden SQLite for the single-process FastAPI runtime.

    WAL allows readers to continue while a writer is active; busy_timeout gives
    short concurrent writes a chance to wait instead of immediately failing with
    "database is locked".
    """
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
    finally:
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class ChatSessionRecord(Base):
    __tablename__ = "chat_sessions"

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    role: Mapped[str] = mapped_column(String(64))
    department: Mapped[str] = mapped_column(String(64))
    shift: Mapped[str | None] = mapped_column(String(32), nullable=True)
    pending_command: Mapped[str | None] = mapped_column(String(128), nullable=True)
    pending_parameters: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ChatMessageRecord(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    role: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AutomationDefinitionRecord(Base):
    __tablename__ = "automation_definitions"

    automation_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    schedule: Mapped[str | None] = mapped_column(String(128), nullable=True)


class AutomationExecutionRecord(Base):
    __tablename__ = "automation_executions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    automation_id: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(32))
    details: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AuditRecord(Base):
    __tablename__ = "audit_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    role: Mapped[str] = mapped_column(String(64))
    department: Mapped[str] = mapped_column(String(64))
    command: Mapped[str] = mapped_column(String(128), index=True)
    operation_type: Mapped[str] = mapped_column(String(32))
    success: Mapped[bool] = mapped_column(Boolean)
    parameters: Mapped[str] = mapped_column(Text, default="{}")
    details: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


REQUIRED_SCHEMA_TABLES = {
    "chat_sessions",
    "chat_messages",
    "automation_definitions",
    "automation_executions",
    "audit_records",
}


def init_db() -> None:
    """Apply Alembic migrations for the runtime database.

    Legacy development databases created before Alembic are stamped at the
    baseline only when all baseline tables already exist. Fresh databases are
    upgraded normally. This keeps the application self-starting while preserving
    Alembic as the schema authority.
    """
    from alembic import command
    from alembic.config import Config

    root = Path(__file__).resolve().parent
    alembic_ini = root / "alembic.ini"
    migrations_dir = root / "migrations"
    if not alembic_ini.exists() or not migrations_dir.exists():
        raise RuntimeError("Alembic migration resources are not available")

    config = Config(str(alembic_ini))
    config.set_main_option("script_location", str(migrations_dir))

    with engine.connect() as connection:
        tables = set(inspect(connection).get_table_names())

    if "alembic_version" not in tables and REQUIRED_SCHEMA_TABLES.issubset(tables):
        command.stamp(config, "head")

    command.upgrade(config, "head")


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
