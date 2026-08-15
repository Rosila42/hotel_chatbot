from hotel_chatbot_v2.core.commands import CommandRegistry
from hotel_chatbot_v2.core.permissions import Identity, PermissionService
from hotel_chatbot_v2.core.router import ChatRouter
from hotel_chatbot_v2.core.session import ChatSession
from hotel_chatbot_v2.integrations.pms.mock_adapter import MockPMSAdapter
from hotel_chatbot_v2.services.automation_service import AutomationService
from hotel_chatbot_v2.services.pms_service import PMSService


def test_write_command_requires_confirmation_then_executes():
    pms = PMSService(MockPMSAdapter())
    permissions = PermissionService()
    automation = AutomationService(pms)
    router = ChatRouter(CommandRegistry(pms, permissions, automation))
    identity = Identity("u1", "housekeeper", "housekeeping")
    session = ChatSession.create(identity)

    pending = router.handle(session, "Create an incident for room 214: AC is broken")
    assert not pending.success
    assert session.pending_command is not None

    confirmed = router.handle(session, "CONFIRM")
    assert confirmed.success
    assert confirmed.command == "CREATE_INCIDENT"
    assert session.pending_command is None
