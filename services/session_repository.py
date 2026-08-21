from __future__ import annotations

import json
from sqlalchemy.orm import Session
from core.permissions import Identity
from core.session import ChatSession
from storage import ChatMessageRecord, ChatSessionRecord

# Domain-level exceptions (decoupled from FastAPI)
class SessionNotFound(Exception): pass
class SessionAccessDenied(Exception): pass
class CorruptedSessionState(Exception): pass

class SessionRepository:
    """Handles database persistence for ChatSessions and ChatMessages."""

    def __init__(self, db: Session):
        self.db = db

    def load_or_create_session(
        self,
        identity: Identity,
        session_id: str | None,
        shift: str | None,
    ) -> ChatSession:
        if session_id:
            record = self.db.get(ChatSessionRecord, session_id)
            if record is None:
                raise SessionNotFound("Session not found")
            if record.user_id != identity.user_id:
                raise SessionAccessDenied("Session does not belong to authenticated user")

            # Efficiently fetch the last 50 messages
            history_rows = (
                self.db.query(ChatMessageRecord)
                .filter(ChatMessageRecord.session_id == session_id)
                .order_by(ChatMessageRecord.created_at.desc())
                .limit(50)
                .all()
            )
            history_rows.reverse() # Restore chronological order

            session = ChatSession(
                session_id=record.session_id,
                identity=identity,
                shift=record.shift,
                created_at=record.created_at,
            )
            session.history = [
                {"role": row.role, "content": row.content} 
                for row in history_rows
            ]
            
            if record.pending_command:
                try:
                    parameters = json.loads(record.pending_parameters or "{}")
                except json.JSONDecodeError as exc:
                    raise CorruptedSessionState("Stored pending action is invalid") from exc
                session.set_pending(record.pending_command, parameters)
            return session

        # Create new session
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
        self.db.flush() # Flush to assign ID without committing transaction
        return session

    def add_message(self, session_id: str, role: str, content: str) -> None:
        self.db.add(
            ChatMessageRecord(session_id=session_id, role=role, content=content)
        )

    def update_session_state(self, session: ChatSession) -> None:
        record = self.db.get(ChatSessionRecord, session.session_id)
        if record is None:
            raise SessionNotFound("Session not found")
        
        record.pending_command = None
        record.pending_parameters = None
        
        if session.pending_command:
            record.pending_command = session.pending_command["command"]
            record.pending_parameters = json.dumps(
                session.pending_command["parameters"]
            )

    def commit(self) -> None:
        """Commit the unit of work."""
        self.db.commit()