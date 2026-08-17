from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Generator

from sqlalchemy import Boolean, DateTime, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


APP_DATA_DIR = Path(
    os.environ.get(
        "XDG_DATA_HOME",
        str(Path.home() / ".local" / "share"),
    )
) / "hotel-chatbot-v2"
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = APP_DATA_DIR / "hotel_chatbot_v2.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
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


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
