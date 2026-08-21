from __future__ import annotations

import re
from datetime import date

from core.commands import CommandRegistry
from core.permissions import Identity
from core.session import ChatSession
from models.commands import CommandRequest, CommandResult, ConfirmationPolicy, ResultKind
from services.command_executor import CommandExecutor


class ChatRouter:
    """Deterministic command pipeline: parse, authorize, validate, confirm, execute."""

    def __init__(
        self,
        registry: CommandRegistry,
        executor: CommandExecutor,
    ) -> None:
        self.registry = registry
        self.executor = executor

    def handle(self, session: ChatSession, message: str) -> CommandResult:
        text = message.strip()
        if not text:
            return CommandResult(ResultKind.INVALID_PARAMS, "Please enter a request.")

        if session.pending_command:
            return self._handle_pending(session, text)

        request = self._interpret(text)
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

    def _interpret(self, text: str) -> CommandRequest | None:
        normalized = text.lower()

        if normalized in {"help", "what can you do", "commands"}:
            return CommandRequest("HELP")
        if "system status" in normalized or normalized == "status":
            return CommandRequest("GET_SYSTEM_STATUS")

        automation_id = self._automation_id(normalized)
        if automation_id:
            if any(word in normalized for word in ("list", "show")) and "automation" in normalized:
                return CommandRequest("LIST_AUTOMATIONS")
            if "enable" in normalized or "activate" in normalized:
                return CommandRequest("ENABLE_AUTOMATION", {"automation_id": automation_id})
            if "disable" in normalized or "deactivate" in normalized:
                return CommandRequest("DISABLE_AUTOMATION", {"automation_id": automation_id})
            if "run" in normalized or "execute" in normalized:
                return CommandRequest("RUN_AUTOMATION", {"automation_id": automation_id})
            if "history" in normalized:
                return CommandRequest("GET_AUTOMATION_HISTORY", {"automation_id": automation_id})
            if "status" in normalized:
                return CommandRequest("GET_AUTOMATION_STATUS", {"automation_id": automation_id})

        if "automation" in normalized and any(word in normalized for word in ("list", "show")):
            return CommandRequest("LIST_AUTOMATIONS")

        if "arrival" in normalized or "checking in" in normalized:
            return CommandRequest("GET_ARRIVALS", {"date": date.today().isoformat()})
        if "departure" in normalized or "checking out" in normalized:
            return CommandRequest("GET_DEPARTURES", {"date": date.today().isoformat()})
        if "guest" in normalized and any(word in normalized for word in ("find", "search", "look up", "lookup")):
            name = self._after_keyword(text, ("guest", "for"))
            if name:
                return CommandRequest("SEARCH_GUEST", {"name": name})
        if "reservation" in normalized:
            reservation_id = self._extract(normalized, r"(?:reservation|booking)\s*#?([a-z0-9-]+)")
            if reservation_id and reservation_id.lower() not in {"for", "status"}:
                return CommandRequest("GET_RESERVATION", {"reservation_id": reservation_id})
        room = self._extract(text, r"room\s*(\d+)")
        if room and "mark" in normalized and "clean" in normalized:
            return CommandRequest("MARK_ROOM_CLEAN", {"room_number": room})
        if room and any(word in normalized for word in ("status", "ready", "dirty", "cleaning", "available")):
            return CommandRequest("GET_ROOM_STATUS", {"room_number": room})
        if "incident" in normalized or "broken" in normalized or "not working" in normalized:
            incident_type = "HOUSEKEEPING" if "clean" in normalized or "housekeeping" in normalized else "MAINTENANCE"
            return CommandRequest(
                "CREATE_INCIDENT",
                {"room_number": room, "incident_type": incident_type, "description": text},
            )
        if "incidents" in normalized:
            return CommandRequest("GET_INCIDENTS", {"status": "OPEN"})
        if "operational summary" in normalized or "hotel summary" in normalized or "daily summary" in normalized:
            return CommandRequest("GET_OPERATIONAL_SUMMARY")
        if any(word in normalized for word in ("breakfast", "checkout time", "check-out time", "policy", "wifi", "wi-fi")):
            return CommandRequest("FAQ_SEARCH", {"query": text})
        return None

    @staticmethod
    def _automation_id(text: str) -> str | None:
        if "morning_arrival_check" in text or "morning arrival check" in text:
            return "MORNING_ARRIVAL_CHECK"
        return None

    @staticmethod
    def _extract(text: str, pattern: str) -> str | None:
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1) if match else None

    @staticmethod
    def _after_keyword(text: str, keywords: tuple[str, ...]) -> str | None:
        lower = text.lower()
        for keyword in keywords:
            index = lower.rfind(keyword)
            if index >= 0:
                candidate = text[index + len(keyword):].strip(" :#,-")
                if candidate:
                    return candidate.removeprefix("for ").strip()
        return None
