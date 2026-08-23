from __future__ import annotations

from sqlalchemy.orm import Session

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
        self.parser = parser or DeterministicParser()

    def handle(
        self,
        session: ChatSession,
        message: str,
        *,
        db: Session | None = None,
    ) -> CommandResult:
        text = message.strip()
        if not text:
            return CommandResult(ResultKind.INVALID_PARAMS, "Please enter a request.")

        if session.pending_command:
            return self._handle_pending(session, text, db=db)

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

        # Gate 1: authorization.
        if not self.registry.permissions.can(session.identity, command.permission):
            return CommandResult(
                ResultKind.DENIED,
                "You are not authorized to perform this action.",
                command=command.name,
            )

        # Gate 2: structural validation.
        errors = command.validate(request.parameters)
        if errors:
            return CommandResult(
                ResultKind.INVALID_PARAMS,
                "Invalid parameters: " + "; ".join(errors),
                command=command.name,
            )

        # Gate 3: explicit confirmation.
        if command.confirmation == ConfirmationPolicy.REQUIRED:
            session.set_pending(command.name, request.parameters)
            return CommandResult(
                ResultKind.AWAITING_CONFIRMATION,
                f"Please confirm: {command.description} ({command.name}). Reply CONFIRM or CANCEL.",
                command=command.name,
            )

        # Gate 4: execute only after all policy gates pass.
        return self.executor.execute(session.identity, request, command, db=db)

    def _handle_pending(
        self,
        session: ChatSession,
        message: str,
        *,
        db: Session | None = None,
    ) -> CommandResult:
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

        if db is not None:
            if not self._claim_pending(db, session, command.name, parameters):
                session.clear_pending()
                return CommandResult(
                    ResultKind.FAILED,
                    "This confirmation was already consumed by another request.",
                    command=command.name,
                )
        else:
            session.clear_pending()

        return self.executor.execute(
            session.identity,
            CommandRequest(command.name, parameters),
            command,
            db=db,
        )

    @staticmethod
    def _claim_pending(db: Session, session: ChatSession, command_name: str, parameters: dict) -> bool:
        from services.session_repository import SessionRepository

        claimed = SessionRepository(db).claim_pending_action(
            session.session_id,
            command_name,
            parameters,
        )
        if claimed:
            session.clear_pending()
        return claimed
