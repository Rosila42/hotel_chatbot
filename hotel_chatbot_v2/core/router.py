from __future__ import annotations

import re
from datetime import date

from hotel_chatbot_v2.core.commands import CommandRegistry
from hotel_chatbot_v2.core.permissions import Identity
from hotel_chatbot_v2.core.session import ChatSession
from hotel_chatbot_v2.models.commands import CommandRequest, CommandResult, ConfirmationPolicy


class ChatRouter:
    """Deterministic natural-language router for the V1 command catalog."""

    def __init__(self, registry: CommandRegistry) -> None:
        self.registry = registry

    def handle(self, session: ChatSession, message: str) -> CommandResult:
        text = message.strip()
        if not text:
            return CommandResult(False, "Please enter a request.")

        normalized = text.lower()
        if session.pending_command:
            if normalized in {"confirm", "confirmed", "yes", "proceed"}:
                pending = session.pending_command
                session.clear_pending()
                return self.registry.execute(
                    session.identity,
                    CommandRequest(pending["command"], pending["parameters"]),
                    confirmed=True,
                )
            if normalized in {"cancel", "cancelled", "no", "abort"}:
                session.clear_pending()
                return CommandResult(True, "Pending action cancelled.")
            return CommandResult(False, "A confirmation is pending. Reply CONFIRM to proceed or CANCEL to abort.")

        request = self._interpret(text)
        if request is None:
            return CommandResult(False, "I could not identify a supported action. Try HELP to see available capabilities.")

        command = self.registry.get(request.name)
        if command and command.confirmation == ConfirmationPolicy.REQUIRED:
            session.set_pending(request.name, request.parameters)
            return CommandResult(
                False,
                f"Please confirm: {command.description} ({request.name}). Reply CONFIRM or CANCEL.",
                command=request.name,
            )

        return self.registry.execute(session.identity, request)

    def _interpret(self, text: str) -> CommandRequest | None:
        normalized = text.lower()

        if normalized in {"help", "what can you do", "commands"}:
            return CommandRequest("HELP")
        if "system status" in normalized or normalized == "status":
            return CommandRequest("GET_SYSTEM_STATUS")
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
        if room and any(word in normalized for word in ("status", "ready", "dirty", "cleaning", "available")):
            return CommandRequest("GET_ROOM_STATUS", {"room_number": room})
        if room and "mark" in normalized and "clean" in normalized:
            return CommandRequest("MARK_ROOM_CLEAN", {"room_number": room})
        if "incident" in normalized or "broken" in normalized or "not working" in normalized:
            incident_type = "HOUSEKEEPING" if "clean" in normalized or "housekeeping" in normalized else "MAINTENANCE"
            return CommandRequest("CREATE_INCIDENT", {"room_number": room, "incident_type": incident_type, "description": text})
        if "open incidents" in normalized or normalized == "incidents" or "incidents" in normalized:
            return CommandRequest("GET_INCIDENTS", {"status": "OPEN"})
        if "operational summary" in normalized or "hotel summary" in normalized or "daily summary" in normalized:
            return CommandRequest("GET_OPERATIONAL_SUMMARY")
        if any(word in normalized for word in ("breakfast", "checkout time", "check-out time", "policy", "wifi", "wi-fi")):
            return CommandRequest("FAQ_SEARCH", {"query": text})
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
