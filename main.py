from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from api.auth import authenticate
from api.schemas import ChatRequest, ChatResponse, ConfirmationInfo, PermissionInfo
from core.commands import CommandRegistry
from core.parser import DeterministicParser
from core.permissions import Identity, PermissionService
from core.router import ChatRouter
from integrations.pms.mock_adapter import MockPMSAdapter
from pms_adapters.real_pms_adapter import RealPMSAdapter
from services.automation_service import AutomationService
from services.automation_worker import AutomationWorker
from services.command_executor import CommandExecutor
from services.pms_service import PMSService
from services.session_repository import (
    CorruptedSessionState,
    SessionAccessDenied,
    SessionNotFound,
    SessionRepository,
)
from storage import get_db, init_db


def _application_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


ROOT = _application_root()
WEB_DIR = ROOT / "web"

# Production integrations remain opt-in; the local demo defaults to the mock PMS.
adapter_choice = os.getenv("HOTEL_CHATBOT_PMS_ADAPTER", "mock").lower()
if adapter_choice == "real":
    _pms = PMSService(RealPMSAdapter())
else:
    _pms = PMSService(MockPMSAdapter())

_permissions = PermissionService()
_automation = AutomationService(_pms)
_commands = CommandRegistry(_permissions)
_executor = CommandExecutor(_pms, _automation, help_provider=_commands.names_for)
_parser = DeterministicParser()
_router = ChatRouter(_commands, _executor, parser=_parser)
_worker = AutomationWorker(_automation)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        init_db()
        _automation.ensure_definitions()
        _worker.start()
        _worker.schedule_morning_arrival_check()
    except Exception:
        _worker.stop()
        raise

    yield

    _worker.stop()


app = FastAPI(title="Hotel PMS Chatbot V2", version="0.1.0", lifespan=lifespan)


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/app/")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _allowed_roles(permission: str | None) -> list[str]:
    if permission is None:
        return ["receptionist", "housekeeper", "manager"]
    return [
        role
        for role, permissions in PermissionService.ROLE_PERMISSIONS.items()
        if permission in permissions
    ]


def _room_status_for(room_number: str | None) -> str | None:
    if not room_number:
        return None
    rooms = _pms.get_room_status(room_number=room_number)
    if not rooms:
        return None
    return getattr(rooms[0].status, "value", str(rooms[0].status))


def _build_observability(
    identity: Identity,
    request: ChatRequest,
    pending_command: dict | None,
    result,
    command_definition,
    parser_request,
    state_before: str | None,
) -> dict:
    command_name = result.command or (
        pending_command.get("command") if pending_command else parser_request.name if parser_request else None
    )
    if parser_request is not None:
        parameters = dict(parser_request.parameters)
    elif pending_command:
        parameters = dict(pending_command.get("parameters", {}))
    else:
        parameters = None

    allowed = bool(command_definition and _permissions.can(identity, command_definition.permission))
    allowed_roles = _allowed_roles(command_definition.permission if command_definition else None)

    normalized_message = request.message.strip().casefold()
    if normalized_message in {"cancel", "cancelled", "no", "abort"} and pending_command:
        confirmation_state = "cancelled"
    elif result.kind.value == "AWAITING_CONFIRMATION":
        confirmation_state = "pending"
    elif pending_command and result.kind.value == "SUCCESS":
        confirmation_state = "confirmed"
    else:
        confirmation_state = "none"

    state_after = None
    if command_name == "MARK_ROOM_CLEAN" and result.kind.value == "SUCCESS" and parameters:
        state_after = _room_status_for(parameters.get("room_number"))

    executed = bool(
        command_definition
        and not pending_command
        and result.kind.value not in {"AWAITING_CONFIRMATION", "DENIED", "UNKNOWN_COMMAND"}
    ) or bool(
        command_definition
        and pending_command
        and result.kind.value == "SUCCESS"
    )

    return {
        "command": command_name,
        "parameters": parameters,
        "parser_source": "deterministic" if parser_request is not None else "pending_session" if pending_command else None,
        "permission": PermissionInfo(
            allowed=allowed,
            role=identity.role,
            allowed_roles=allowed_roles,
        ),
        "confirmation": ConfirmationInfo(state=confirmation_state),
        "pms_adapter": type(_pms.adapter).__name__,
        "state_before": state_before,
        "state_after": state_after,
        "audit_recorded": executed,
    }


@app.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    identity: Identity = Depends(authenticate),
    db: Session = Depends(get_db),
) -> ChatResponse:
    session_repo = SessionRepository(db)
    parser_request = None
    command_definition = None
    pending_command = None
    state_before = None

    try:
        session = session_repo.load_or_create_session(identity, request.session_id, request.shift)
        session_repo.add_message(session.session_id, "user", request.message)

        pending_command = dict(session.pending_command) if session.pending_command else None
        if pending_command:
            command_definition = _commands.get(pending_command["command"])
            if pending_command["command"] == "MARK_ROOM_CLEAN":
                state_before = _room_status_for(pending_command.get("parameters", {}).get("room_number"))
        else:
            parser_request = _parser.parse(request.message)
            if parser_request:
                command_definition = _commands.get(parser_request.name)
                if parser_request.name == "MARK_ROOM_CLEAN":
                    state_before = _room_status_for(parser_request.parameters.get("room_number"))

        result = _router.handle(session, request.message, db=db)

        session_repo.update_session_state(session)
        session_repo.add_message(session.session_id, "assistant", result.message)
        session_repo.commit()
    except SessionNotFound as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail="Session not found") from exc
    except SessionAccessDenied as exc:
        db.rollback()
        raise HTTPException(status_code=403, detail="Session does not belong to authenticated user") from exc
    except CorruptedSessionState as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Stored pending action is invalid") from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Request could not be completed") from exc

    meta = _build_observability(
        identity,
        request,
        pending_command,
        result,
        command_definition,
        parser_request,
        state_before,
    )

    return ChatResponse(
        session_id=session.session_id,
        success=result.success,
        message=result.message,
        command=meta["command"],
        parameters=meta["parameters"],
        data=result.data,
        parser_source=meta["parser_source"],
        permission=meta["permission"],
        confirmation=meta["confirmation"],
        pms_adapter=meta["pms_adapter"],
        state_before=meta["state_before"],
        state_after=meta["state_after"],
        audit_recorded=meta["audit_recorded"],
    )


@app.get("/capabilities")
def capabilities(identity: Identity = Depends(authenticate)) -> dict[str, list[str]]:
    return {"commands": _commands.names_for(identity)}


app.mount("/app", StaticFiles(directory=WEB_DIR, html=True), name="web")
