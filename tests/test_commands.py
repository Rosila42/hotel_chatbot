from datetime import date

from core.commands import CommandRegistry
from core.permissions import Identity, PermissionService
from integrations.pms.mock_adapter import MockPMSAdapter
from models.commands import CommandRequest, ResultKind
from services.command_executor import CommandExecutor
from services.pms_service import PMSService
from storage import init_db


def build_services():
    init_db()
    pms = PMSService(MockPMSAdapter())
    return pms, PermissionService()


def test_registry_contains_complete_v1_catalog():
    _, permissions = build_services()
    registry = CommandRegistry(permissions)
    names = {command.name for command in registry.all()}

    assert len(names) == 19
    assert "GET_ARRIVALS" in names
    assert "CREATE_INCIDENT" in names
    assert "RUN_AUTOMATION" in names


def test_command_validation_rejects_missing_required_parameters():
    _, permissions = build_services()
    registry = CommandRegistry(permissions)
    command = registry.get("MARK_ROOM_CLEAN")

    assert command is not None
    errors = command.validate({})
    assert errors
    assert "room_number" in errors[0]


def test_executor_can_execute_authorized_read():
    pms, permissions = build_services()
    registry = CommandRegistry(permissions)
    executor = CommandExecutor(pms)
    identity = Identity("u1", "receptionist", "reception")
    command = registry.get("GET_ARRIVALS")

    assert command is not None
    result = executor.execute(
        identity,
        CommandRequest("GET_ARRIVALS", {"date": date.today().isoformat()}),
        command,
    )

    assert result.kind is ResultKind.SUCCESS
