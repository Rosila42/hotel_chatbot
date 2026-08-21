from unittest.mock import Mock

from core.commands import CommandRegistry
from core.permissions import Identity, PermissionService
from core.router import ChatRouter
from core.session import ChatSession
from models.commands import CommandRequest, CommandResult, ResultKind
from services.command_executor import CommandExecutor
from services.pms_service import PMSService
from integrations.pms.mock_adapter import MockPMSAdapter
from storage import init_db


class RouterTestBuilder:
    def __init__(self):
        init_db()
        self.permissions = PermissionService()
        self.pms = PMSService(MockPMSAdapter())
        self.registry = CommandRegistry(self.permissions)
        self.executor = Mock(spec=CommandExecutor)
        self.router = ChatRouter(self.registry, self.executor)

    def session(self, role: str, department: str) -> ChatSession:
        return ChatSession.create(Identity(f"{role}-1", role, department))


def build_router() -> RouterTestBuilder:
    return RouterTestBuilder()


def test_automation_name_does_not_get_misclassified_as_arrivals():
    builder = build_router()
    request = builder.router._interpret("enable morning arrival check")

    assert request is not None
    assert request.name == "ENABLE_AUTOMATION"
    assert request.parameters["automation_id"] == "MORNING_ARRIVAL_CHECK"


def test_required_confirmation_is_enforced_by_router():
    builder = build_router()
    session = builder.session("manager", "management")
    builder.executor.execute.return_value = CommandResult(
        ResultKind.SUCCESS,
        "enabled",
        command="ENABLE_AUTOMATION",
    )

    result = builder.router.handle(session, "enable morning arrival check")

    assert result.kind is ResultKind.AWAITING_CONFIRMATION
    assert result.command == "ENABLE_AUTOMATION"
    assert session.pending_command is not None
    builder.executor.execute.assert_not_called()


def test_flaw_3_contract_denied_before_confirmation_or_execution():
    builder = build_router()
    session = builder.session("receptionist", "reception")

    result = builder.router.handle(session, "the AC in room 214 is broken")

    assert result.kind is ResultKind.DENIED
    assert session.pending_command is None
    builder.executor.execute.assert_not_called()


def test_permission_gate_runs_before_structural_validation():
    builder = build_router()
    session = builder.session("receptionist", "reception")

    request = CommandRequest("CREATE_INCIDENT", {})
    command = builder.registry.get(request.name)
    assert command is not None
    assert command.validate(request.parameters)
    session.pending_command = {"command": request.name, "parameters": request.parameters}

    session.clear_pending()
    result = builder.router.handle(session, "the AC in room 214 is broken")

    assert result.kind is ResultKind.DENIED
    assert result.kind is not ResultKind.INVALID_PARAMS
    builder.executor.execute.assert_not_called()


def test_confirmation_resumes_after_permission_and_validation_checks():
    builder = build_router()
    session = builder.session("manager", "management")
    builder.executor.execute.return_value = CommandResult(
        ResultKind.SUCCESS,
        "incident created",
        command="CREATE_INCIDENT",
    )

    first = builder.router.handle(session, "the AC in room 214 is broken")
    assert first.kind is ResultKind.AWAITING_CONFIRMATION
    assert session.pending_command is not None

    result = builder.router.handle(session, "CONFIRM")

    assert result.kind is ResultKind.SUCCESS
    assert session.pending_command is None
    builder.executor.execute.assert_called_once()
    request = builder.executor.execute.call_args.args[1]
    assert isinstance(request, CommandRequest)
    assert request.name == "CREATE_INCIDENT"


def test_pending_confirmation_does_not_accept_ambiguous_message():
    builder = build_router()
    session = builder.session("manager", "management")

    first = builder.router.handle(session, "the AC in room 214 is broken")
    assert first.kind is ResultKind.AWAITING_CONFIRMATION

    result = builder.router.handle(session, "yes please create it")

    assert result.kind is ResultKind.AWAITING_CONFIRMATION
    assert session.pending_command is not None
    builder.executor.execute.assert_not_called()


def test_cancel_clears_pending_command_without_execution():
    builder = build_router()
    session = builder.session("manager", "management")

    first = builder.router.handle(session, "the AC in room 214 is broken")
    assert first.kind is ResultKind.AWAITING_CONFIRMATION

    result = builder.router.handle(session, "CANCEL")

    assert result.kind is ResultKind.SUCCESS
    assert session.pending_command is None
    builder.executor.execute.assert_not_called()
