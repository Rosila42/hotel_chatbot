from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from hotel_chatbot_v2.api.auth import authenticate
from hotel_chatbot_v2.api.schemas import ChatRequest, ChatResponse
from hotel_chatbot_v2.core.commands import CommandRegistry
from hotel_chatbot_v2.core.permissions import Identity, PermissionService
from hotel_chatbot_v2.core.router import ChatRouter
from hotel_chatbot_v2.core.session import ChatSession
from hotel_chatbot_v2.integrations.pms.mock_adapter import MockPMSAdapter
from hotel_chatbot_v2.services.automation_service import AutomationService
from hotel_chatbot_v2.services.automation_worker import AutomationWorker
from hotel_chatbot_v2.services.pms_service import PMSService
from hotel_chatbot_v2.storage import ChatMessageRecord, ChatSessionRecord, get_db, init_db

app = FastAPI(title="Hotel PMS Chatbot V2", version="0.1.0")

_pms = PMSService(MockPMSAdapter())
_permissions = PermissionService()
_automation = AutomationService(_pms)
_commands = CommandRegistry(_pms, _permissions, _automation)
_router = ChatRouter(_commands)
_worker = AutomationWorker(_automation)
init_db()
_worker.start()
_worker.schedule_morning_arrival_check()


def _load_or_create_session(
    db: Session, identity: Identity, session_id: str | None, shift: str | None
) -> ChatSession:
    if session_id:
        record = db.get(ChatSessionRecord, session_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Session not found")
        if record.user_id != identity.user_id:
            raise HTTPException(status_code=403, detail="Session does not belong to authenticated user")
        history_rows = (
            db.query(ChatMessageRecord)
            .filter(ChatMessageRecord.session_id == session_id)
            .order_by(ChatMessageRecord.created_at.asc())
            .all()
        )
        session = ChatSession(
            session_id=record.session_id,
            identity=identity,
            shift=record.shift,
            created_at=record.created_at,
        )
        session.history = [{"role": row.role, "content": row.content} for row in history_rows][-50:]
        return session

    session = ChatSession.create(identity, shift=shift)
    db.add(
        ChatSessionRecord(
            session_id=session.session_id,
            user_id=identity.user_id,
            role=identity.role,
            department=identity.department,
            shift=shift,
        )
    )
    db.commit()
    return session


def _persist_message(db: Session, session_id: str, role: str, content: str) -> None:
    db.add(ChatMessageRecord(session_id=session_id, role=role, content=content))
    db.commit()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    identity: Identity = Depends(authenticate),
    db: Session = Depends(get_db),
) -> ChatResponse:
    session = _load_or_create_session(db, identity, request.session_id, request.shift)
    _persist_message(db, session.session_id, "user", request.message)

    result = _router.handle(session, request.message)
    _persist_message(db, session.session_id, "assistant", result.message)

    return ChatResponse(
        session_id=session.session_id,
        success=result.success,
        message=result.message,
        command=result.command,
        data=result.data,
    )


@app.get("/capabilities")
def capabilities(identity: Identity = Depends(authenticate)) -> dict[str, list[str]]:
    return {"commands": [command.name for command in _commands.list_for(identity)]}
