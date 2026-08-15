from datetime import date

from core.commands import CommandRegistry
from core.permissions import Identity, PermissionService
from integrations.pms.mock_adapter import MockPMSAdapter
from models.commands import CommandRequest
from services.automation_service import AutomationService
from services.pms_service import PMSService
from storage import init_db


def build_registry():
    init_db()
    pms = PMSService(MockPMSAdapter())
    automation = AutomationService(pms)
    return CommandRegistry(pms, PermissionService(), automation)


def test_receptionist_can_read_arrivals():
    registry = build_registry()
    identity = Identity("u1", "receptionist", "reception")
    result = registry.execute(identity, CommandRequest("GET_ARRIVALS", {"date": date.today().isoformat()}))
    assert result.success


def test_receptionist_cannot_mark_room_clean():
    registry = build_registry()
    identity = Identity("u1", "receptionist", "reception")
    result = registry.execute(identity, CommandRequest("MARK_ROOM_CLEAN", {"room_number": "214"}))
    assert not result.success
