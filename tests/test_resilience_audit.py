from __future__ import annotations

import json

from core.commands import CommandRegistry
from core.permissions import Identity, PermissionService
from integrations.pms.mock_adapter import MockPMSAdapter
from models.commands import CommandRequest
from services.pms_service import PMSService
from services.automation_service import AutomationService
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


def test_command_execution_creates_audit_record():
    init_db()
    registry = CommandRegistry(PMSService(MockPMSAdapter()), PermissionService(), AutomationService(PMSService(MockPMSAdapter())))
    identity = Identity("audit-user", "housekeeper", "housekeeping")
    result = registry.execute(identity, CommandRequest("MARK_ROOM_CLEAN", {"room_number": "214"}))
    assert result.success

    with SessionLocal() as db:
        row = db.query(AuditRecord).filter(AuditRecord.user_id == "audit-user").order_by(AuditRecord.id.desc()).first()
        assert row is not None
        assert row.command == "MARK_ROOM_CLEAN"
        assert row.success is True
        assert json.loads(row.parameters)["room_number"] == "214"
