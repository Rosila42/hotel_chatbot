from __future__ import annotations

import json

from core.commands import CommandRegistry
from core.permissions import Identity, PermissionService
from integrations.pms.mock_adapter import MockPMSAdapter
from models.commands import CommandRequest, ResultKind
from services.audit_service import AuditService
from services.automation_service import AutomationService
from services.command_executor import CommandExecutor
from services.pms_service import PMSService
from storage import AuditRecord, SessionLocal, init_db


def test_pms_read_retries_connection_error():
    class FlakyAdapter(MockPMSAdapter):
        calls = 0

        def get_arrivals(self, on_date):
            self.calls += 1
            if self.calls < 3:
                raise ConnectionError("temporary PMS failure")
            return super().get_arrivals(on_date)

    adapter = FlakyAdapter()
    service = PMSService(adapter, read_retries=2)
    assert service.get_arrivals(__import__("datetime").date.today())
    assert adapter.calls == 3


def test_pms_write_is_not_retried():
    class FailingWriteAdapter(MockPMSAdapter):
        calls = 0

        def mark_room_clean(self, room_number):
            self.calls += 1
            raise ConnectionError("write failed")

    adapter = FailingWriteAdapter()
    service = PMSService(adapter, read_retries=2)
    try:
        service.mark_room_clean("214")
    except ConnectionError:
        pass
    assert adapter.calls == 1


def test_command_execution_creates_structured_audit_record():
    init_db()
    pms = PMSService(MockPMSAdapter())
    permissions = PermissionService()
    registry = CommandRegistry(permissions)
    executor = CommandExecutor(pms, AutomationService(pms), audit=AuditService())
    identity = Identity("audit-user", "housekeeper", "housekeeping")
    command = registry.get("MARK_ROOM_CLEAN")

    assert command is not None
    result = executor.execute(
        identity,
        CommandRequest("MARK_ROOM_CLEAN", {"room_number": "214"}),
        command,
    )
    assert result.kind is ResultKind.SUCCESS

    with SessionLocal() as db:
        row = (
            db.query(AuditRecord)
            .filter(AuditRecord.user_id == "audit-user")
            .order_by(AuditRecord.id.desc())
            .first()
        )
        assert row is not None
        assert row.command == "MARK_ROOM_CLEAN"
        assert row.success is True
        assert json.loads(row.parameters)["room_number"] == "214"
        assert json.loads(row.details)["result_kind"] == ResultKind.SUCCESS.value


def test_automation_audit_uses_result_kind_contract():
    init_db()
    pms = PMSService(MockPMSAdapter())
    service = AutomationService(pms)

    result = service.enable("MORNING_ARRIVAL_CHECK")

    assert result["enabled"] is True
