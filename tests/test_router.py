from datetime import date

from core.commands import CommandRegistry
from core.permissions import Identity, PermissionService
from core.router import ChatRouter
from core.session import ChatSession
from integrations.pms.mock_adapter import MockPMSAdapter
from services.automation_service import AutomationService
from services.pms_service import PMSService
from storage import init_db


def build_router():
    init_db()
    pms = PMSService(MockPMSAdapter())
    automation = AutomationService(pms)
    return ChatRouter(CommandRegistry(pms, PermissionService(), automation))


def test_automation_name_does_not_get_misclassified_as_arrivals():
    router = build_router()
    session = ChatSession.create(Identity("manager-1", "manager", "management"))
    request = router._interpret("enable morning arrival check")
    assert request is not None
    assert request.name == "ENABLE_AUTOMATION"
    assert request.parameters["automation_id"] == "MORNING_ARRIVAL_CHECK"


def test_required_confirmation_is_enforced_by_router():
    router = build_router()
    session = ChatSession.create(Identity("manager-1", "manager", "management"))
    result = router.handle(session, "enable morning arrival check")
    assert result.command == "ENABLE_AUTOMATION"
    assert result.success is False
    assert session.pending_command is not None
