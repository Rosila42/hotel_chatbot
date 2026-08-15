from __future__ import annotations

from fastapi import Depends, FastAPI

from hotel_chatbot_v2.api.auth import authenticate
from hotel_chatbot_v2.api.schemas import ChatRequest, ChatResponse
from hotel_chatbot_v2.core.commands import CommandRegistry
from hotel_chatbot_v2.core.permissions import Identity, PermissionService
from hotel_chatbot_v2.core.router import ChatRouter
from hotel_chatbot_v2.core.session import ChatSession
from hotel_chatbot_v2.integrations.pms.mock_adapter import MockPMSAdapter
from hotel_chatbot_v2.services.pms_service import PMSService

app = FastAPI(title="Hotel PMS Chatbot V2", version="0.1.0")

_pms = PMSService(MockPMSAdapter())
_permissions = PermissionService()
_commands = CommandRegistry(_pms, _permissions)
_router = ChatRouter(_commands)
_sessions: dict[str, ChatSession] = {}


def _get_session(identity: Identity, session_id: str | None, shift: str | None) -> ChatSession:
    if session_id:
        session = _sessions.get(session_id)
        if session is None:
            raise ValueError("Session not found")
        if session.identity.user_id != identity.user_id:
            raise PermissionError("Session does not belong to authenticated user")
        return session
    session = ChatSession.create(identity, shift=shift)
    _sessions[session.session_id] = session
    return session


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, identity: Identity = Depends(authenticate)) -> ChatResponse:
    try:
        session = _get_session(identity, request.session_id, request.shift)
    except PermissionError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    session.add_message("user", request.message)
    result = _router.handle(identity, request.message)
    session.add_message("assistant", result.message)

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
