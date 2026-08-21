from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from api.auth import authenticate
from api.schemas import ChatRequest, ChatResponse
from core.commands import CommandRegistry
from core.permissions import Identity, PermissionService
from core.router import ChatRouter
from integrations.pms.mock_adapter import MockPMSAdapter
from services.automation_service import AutomationService
from services.automation_worker import AutomationWorker
from services.pms_service import PMSService
from services.session_repository import (
    SessionRepository, SessionNotFound, SessionAccessDenied, CorruptedSessionState
)
from storage import get_db, init_db

def _application_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent

ROOT = _application_root()
WEB_DIR = ROOT / "web"

_pms = PMSService(MockPMSAdapter())
_permissions = PermissionService()
_automation = AutomationService(_pms)
_commands = CommandRegistry(_permissions)
_executor = CommandExecutor(_pms, _automation)
_router = ChatRouter(_commands)
_worker = AutomationWorker(_automation)
_router = ChatRouter(_commands, _executor, _permissions)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    try:
        init_db()
        _worker.start()
        _worker.schedule_morning_arrival_check()
    except Exception:
        # Ensure worker is stopped if startup fails before yield
        if hasattr(_worker, "stop"):
            _worker.stop()
        raise
        
    yield
    
    # Shutdown logic
    if hasattr(_worker, "stop"):
        _worker.stop()

app = FastAPI(title="Hotel PMS Chatbot V2", version="0.1.0", lifespan=lifespan)

@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/app/")

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    identity: Identity = Depends(authenticate),
    db: Session = Depends(get_db),
) -> ChatResponse:
    session_repo = SessionRepository(db)
    
    try:
        session = session_repo.load_or_create_session(
            identity, request.session_id, request.shift
        )
        session_repo.add_message(session.session_id, "user", request.message)

        result = _router.handle(session, request.message)
        
        session_repo.update_session_state(session)
        session_repo.add_message(session.session_id, "assistant", result.message)
        
        # Single transactional commit for the entire request
        session_repo.commit()
    except SessionNotFound:
        raise HTTPException(status_code=404, detail="Session not found")
    except SessionAccessDenied:
        raise HTTPException(status_code=403, detail="Session does not belong to authenticated user")
    except CorruptedSessionState:
        raise HTTPException(status_code=500, detail="Stored pending action is invalid")

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

app.mount("/app", StaticFiles(directory=WEB_DIR, html=True), name="web")