from __future__ import annotations

import json

from sqlalchemy import update
from sqlalchemy.orm import Session

from core.permissions import Identity
from core.session import ChatSession
from storage import ChatMessageRecord, ChatSessionRecord


class SessionNotFound(Exception):
    pass


class SessionAccessDenied(Exception):
    pass


class CorruptedSessionState(Exception):
    pass


class SessionRepository:
    """Handles database persistence for ChatSessions and ChatMessages."""

    def __init__(self, db: Session):
        self.db = db

    def load_or_create_session(self, identity: Identity, session_id: str | None, shift: str | None) -> ChatSession:
        if session_id:
            record = self.db.get(ChatSessionRecord, session_id)
            if record is None:
                raise SessionNotFound("Session not found")
            if record.user_id != identity.user_id:
                raise SessionAccessDenied("Session does not belong to authenticated user")

            history_rows = (
                self.db.query(ChatMessageRecord)
                .filter(ChatMessageRecord.session_id == session_id)
                .order_by(ChatMessageRecord.created_at.desc())
                .limit(50)
                .all()
            )
            history_rows.reverse()

            session = ChatSession(
                session_id=record.session_id,
                identity=identity,
                shift=record.shift,
                created_at=record.created_at,
            )
            session.history = [{"role": row.role, "content": row.content} for row in history_rows]

            if record.pending_command:
                try:
                    parameters = json.loads(record.pending_parameters or "{}")
                except json.JSONDecodeError as exc:
                    raise CorruptedSessionState("Stored pending action is invalid") from exc
                session.set_pending(record.pending_command, parameters)
            return session

        session = ChatSession.create(identity, shift=shift)
        self.db.add(
            ChatSessionRecord(
                session_id=session.session_id,
                user_id=identity.user_id,
                role=identity.role,
                department=identity.department,
                shift=shift,
            )
        )
        self.db.flush()
        return session

    def add_message(self, session_id: str, role: str, content: str) -> None:
        self.db.add(ChatMessageRecord(session_id=session_id, role=role, content=content))

    def update_session_state(self, session: ChatSession) -> None:
        record = self.db.get(ChatSessionRecord, session.session_id)
        if record is None:
            raise SessionNotFound("Session not found")

        record.pending_command = None
        record.pending_parameters = None
        if session.pending_command:
            record.pending_command = session.pending_command["command"]
            record.pending_parameters = json.dumps(session.pending_command["parameters"])

    def claim_pending_action(self, session_id: str, command_name: str, parameters: dict) -> bool:
        """Atomically consume a pending action before its side effect."""
        stored_parameters = json.dumps(parameters)
        statement = (
            update(ChatSessionRecord)
            .where(ChatSessionRecord.session_id == session_id)
            .where(ChatSessionRecord.pending_command == command_name)
            .where(ChatSessionRecord.pending_parameters == stored_parameters)
            .values(pending_command=None, pending_parameters=None)
        )
        result = self.db.execute(statement)
        if result.rowcount != 1:
            # No row was changed, so the transaction still contains the caller's
            # uncommitted request messages. Leave them intact for the response audit.
            return False
        self.db.commit()
        return True

    def commit(self) -> None:
        self.db.commit()
