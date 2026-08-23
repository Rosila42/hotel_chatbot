from __future__ import annotations

from core.commands import CommandRegistry
from core.parser import DeterministicParser, Parser
from core.permissions import Identity
from core.session import ChatSession
from models.commands import CommandRequest, CommandResult, ConfirmationPolicy, ResultKind
from services.command_executor import CommandExecutor


class ChatRouter:
    """Deterministic policy pipeline: parse, authorize, validate, confirm, execute."""

    def __init__(
        self,
        registry: CommandRegistry,
        executor: CommandExecutor,
        parser: Parser | None = None,
    ) -> None:
        self.registry = registry
        self.executor = executor
        # The parser is deliberately injected so future LLM parsing can implement the
        # same contract without creating a second execution path around this router.
        self.parser = parser or DeterministicParser()

    def handle(self, session: ChatSession, message: str) -> CommandResult:
        text = message.strip()
        if not text:
            return CommandResult(ResultKind.INVALID_PARAMS, "Please enter a request.")

        if session.pending_command:
            return self._handle_pending(session, text)

        # Parsing ends at CommandRequest. Authorization and every trusted policy gate
        # remain exclusively in this router.
        request = self.parser.parse(text)
        if request is None:
            return CommandResult(
                ResultKind.UNKNOWN_COMMAND,
                "I could not identify a supported action. Try HELP to see available capabilities.",
            )

        command = self.registry.get(request.name)
        if command is None:
            return CommandResult(
                ResultKind.UNKNOWN_COMMAND,
                f"Unknown command: {request.name}",
                command=request.name,
            )

        # Gate 1: authorization. Do not validate parameters or reveal the command contract
        # to an identity that is not permitted to use the command.
        if not self.registry.permissions.can(session.identity, command.permission):
            return CommandResult(
                ResultKind.DENIED,
                "You are not authorized to perform this action.",
                command=command.name,
            )

        # Gate 2: structural validation. No PMS/service I/O occurs here.
        errors = command.validate(request.parameters)
        if errors:
            return CommandResult(
                ResultKind.INVALID_PARAMS,
                "Invalid parameters: " + "; ".join(errors),
                command=command.name,
            )

        # Gate 3: explicit confirmation for commands that require it.
        if command.confirmation == ConfirmationPolicy.REQUIRED:
            session.set_pending(command.name, request.parameters)
            return CommandResult(
                ResultKind.AWAITING_CONFIRMATION,
                f"Please confirm: {command.description} ({command.name}). Reply CONFIRM or CANCEL.",
                command=command.name,
            )

        # Gate 4: execute only after all policy gates pass.
        return self.executor.execute(session.identity, request, command)

    def _handle_pending(self, session: ChatSession, message: str) -> CommandResult:
        normalized = message.casefold()
        if normalized in {"cancel", "cancelled", "no", "abort"}:
            session.clear_pending()
            return CommandResult(ResultKind.SUCCESS, "Pending action cancelled.")

        if normalized not in {"confirm", "confirmed", "yes", "proceed"}:
            return CommandResult(
                ResultKind.AWAITING_CONFIRMATION,
                "A confirmation is pending. Reply CONFIRM to proceed or CANCEL to abort.",
            )

        pending = session.pending_command
        command_name = pending["command"]
        parameters = dict(pending["parameters"])
        command = self.registry.get(command_name)

        if command is None:
            session.clear_pending()
            return CommandResult(
                ResultKind.UNKNOWN_COMMAND,
                f"Unknown pending command: {command_name}",
                command=command_name,
            )

        # Re-check authorization and validation at resume time. This prevents a stale
        # pending action from executing after the user's effective capabilities change.
        if not self.registry.permissions.can(session.identity, command.permission):
            session.clear_pending()
            return CommandResult(
                ResultKind.DENIED,
                "You are not authorized to perform this action.",
                command=command.name,
            )

        errors = command.validate(parameters)
        if errors:
            session.clear_pending()
            return CommandResult(
                ResultKind.INVALID_PARAMS,
                "Invalid parameters: " + "; ".join(errors),
                command=command.name,
            )

        session.clear_pending()
        return self.executor.execute(
            session.identity,
            CommandRequest(command.name, parameters),
            command,
        )
