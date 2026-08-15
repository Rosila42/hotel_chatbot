from datetime import date

from hotel_chatbot_v2.core.commands import CommandRegistry
from hotel_chatbot_v2.core.permissions import Identity, PermissionService
from hotel_chatbot_v2.integrations.pms.mock_adapter import MockPMSAdapter
from hotel_chatbot_v2.models.commands import CommandRequest
from hotel_chatbot_v2.services.automation_service import AutomationService
from hotel_chatbot_v2.services.pms_service import PMSService


def build_registry():
    pms = PMSService(MockPMSAdapter())
    permissions = PermissionService()
    automation = AutomationService(pms)
    return CommandRegistry(pms, permissions, automation)


def test_receptionist_can_read_arrivals():
    registry = build_registry()
    identity = Identity("u1", "receptionist", "reception")
    result = registry.execute(identity, CommandRequest("GET_ARRIVALS", {"date": date.today().isoformat()}))
    assert result.success
    assert result.command == "GET_ARRIVALS"


def test_receptionist_cannot_mark_room_clean():
    registry = build_registry()
    identity = Identity("u1", "receptionist", "reception")
    result = registry.execute(identity, CommandRequest("MARK_ROOM_CLEAN", {"room_number": "214"}))
    assert not result.success
    assert "not authorized" in result.message.lower()


def test_manager_can_run_morning_automation():
    registry = build_registry()
    identity = Identity("u2", "manager", "management")
    result = registry.execute(identity, CommandRequest("RUN_AUTOMATION", {"automation_id": "MORNING_ARRIVAL_CHECK"}))
    assert result.success
    assert result.command == "RUN_AUTOMATION"
