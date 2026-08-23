from __future__ import annotations

import ast
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.permissions import Identity
from integrations.pms.mock_adapter import MockPMSAdapter
from models.commands import CommandRequest
from models.pms import RoomStatus
from services.audit_service import AuditEvent, AuditService
from services.automation_service import (
    AutomationBusyError,
    AutomationDisabledError,
    AutomationExecutionError,
    AutomationService,
)
from services.pms_service import PMSService
from services.session_repository import SessionRepository
from storage import Base, ChatSessionRecord


@pytest.fixture()
def isolated_session_factory(tmp_path, monkeypatch):
    database = tmp_path / "hardening.db"
    engine = create_engine(f"sqlite:///{database}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def test_confirmation_claim_is_single_use(isolated_session_factory):
    factory = isolated_session_factory
    identity = Identity("manager-1", "manager", "management")
    session_id = "hardening-session"

    with factory() as db:
        db.add(
            ChatSessionRecord(
                session_id=session_id,
                user_id=identity.user_id,
                role=identity.role,
                department=identity.department,
                shift="morning",
                pending_command="CREATE_INCIDENT",
                pending_parameters='{"room_number": "214", "incident_type": "MAINTENANCE", "description": "AC"}',
            )
        )
        db.commit()

    with factory() as first, factory() as second:
        first_result = SessionRepository(first).claim_pending_action(
            session_id,
            "CREATE_INCIDENT",
            {"room_number": "214", "incident_type": "MAINTENANCE", "description": "AC"},
        )
        second_result = SessionRepository(second).claim_pending_action(
            session_id,
            "CREATE_INCIDENT",
            {"room_number": "214", "incident_type": "MAINTENANCE", "description": "AC"},
        )

    assert first_result is True
    assert second_result is False


def test_request_scoped_audit_stays_in_supplied_transaction(isolated_session_factory):
    factory = isolated_session_factory
    identity = Identity("manager-1", "manager", "management")

    with factory() as db:
        AuditService.record(
            AuditEvent(
                identity=identity,
                command="HELP",
                operation_type="READ",
                result_kind=__import__("models.commands", fromlist=["ResultKind"]).ResultKind.SUCCESS,
            ),
            db=db,
        )
        assert db.query(type(__import__("storage", fromlist=["AuditRecord"]).AuditRecord)).count() == 1
        db.rollback()

    with factory() as db:
        assert db.query(type(__import__("storage", fromlist=["AuditRecord"]).AuditRecord)).count() == 0


def test_not_ready_filter_matches_parser_output():
    pms = PMSService(MockPMSAdapter())
    rooms = pms.get_room_status(filter_name="not_ready")

    assert rooms
    assert all(room.status != RoomStatus.READY for room in rooms)


def test_mock_incident_ids_are_unique():
    adapter = MockPMSAdapter()
    ids = {adapter.create_incident("214", "MAINTENANCE", f"problem {index}").incident_id for index in range(100)}

    assert len(ids) == 100


def test_disabled_automation_is_rejected(monkeypatch):
    service = object.__new__(AutomationService)
    service.pms = PMSService(MockPMSAdapter())
    service._run_locks = {"MORNING_ARRIVAL_CHECK": __import__("threading").Lock()}
    monkeypatch.setattr(service, "_record", lambda _: __import__("storage", fromlist=["AutomationDefinitionRecord"]).AutomationDefinitionRecord(automation_id="MORNING_ARRIVAL_CHECK", enabled=False))

    with pytest.raises(AutomationDisabledError):
        service.run("MORNING_ARRIVAL_CHECK")


def test_automation_overlap_is_rejected(monkeypatch):
    service = object.__new__(AutomationService)
    service.pms = PMSService(MockPMSAdapter())
    lock = __import__("threading").Lock()
    lock.acquire()
    service._run_locks = {"MORNING_ARRIVAL_CHECK": lock}
    monkeypatch.setattr(service, "_record", lambda _: __import__("storage", fromlist=["AutomationDefinitionRecord"]).AutomationDefinitionRecord(automation_id="MORNING_ARRIVAL_CHECK", enabled=True))

    try:
        with pytest.raises(AutomationBusyError):
            service.run("MORNING_ARRIVAL_CHECK")
    finally:
        lock.release()


def test_automation_failure_is_not_returned_as_success(monkeypatch):
    service = object.__new__(AutomationService)
    service.pms = PMSService(MockPMSAdapter())
    service._run_locks = {"MORNING_ARRIVAL_CHECK": __import__("threading").Lock()}
    monkeypatch.setattr(service, "_record", lambda _: __import__("storage", fromlist=["AutomationDefinitionRecord"]).AutomationDefinitionRecord(automation_id="MORNING_ARRIVAL_CHECK", enabled=True))
    monkeypatch.setattr(service, "_record_execution", lambda *args, **kwargs: None)
    monkeypatch.setattr(AuditService, "record_system", lambda *args, **kwargs: None)

    def fail(*args, **kwargs):
        raise RuntimeError("pms unavailable")

    monkeypatch.setattr(service.pms, "get_room_status", fail)

    with pytest.raises(AutomationExecutionError) as exc_info:
        service.run("MORNING_ARRIVAL_CHECK")

    assert exc_info.value.details["status"] == "FAILED"


def test_launcher_disables_terminal_and_network_bind_is_opt_in():
    install_script = Path("install_v2.sh").read_text(encoding="utf-8")
    run_script = Path("run_v2.sh").read_text(encoding="utf-8")

    assert "Terminal=false" in install_script
    assert "ALLOW_INSECURE_NETWORK_DEMO" in run_script
    assert "Refusing non-loopback bind" in run_script


def test_shift_change_clears_transcript():
    javascript = Path("web/app.js").read_text(encoding="utf-8")
    tree = ast.parse("x = 1")
    assert tree is not None
    assert "shift.addEventListener(\"change\"" in javascript
    assert "resetConversation(" in javascript
