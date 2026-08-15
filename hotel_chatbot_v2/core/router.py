from __future__ import annotations

import re
from datetime import date

from hotel_chatbot_v2.core.commands import CommandRegistry
from hotel_chatbot_v2.core.permissions import Identity
from hotel_chatbot_v2.models.commands import CommandRequest, CommandResult


class ChatRouter:
    """Deterministic natural-language router for the V1 command catalog."""

    def __init__(self, registry: CommandRegistry) -> None:
        self.registry = registry

    def handle(self, identity: Identity, message: str) -> CommandResult:
        text = message.strip()
        if not text:
            return CommandResult(False, "Please enter a request.")

        request = self._interpret(text)
        if request is None:
            return CommandResult(False, "I could not identify a supported action. Try HELP to see available capabilities.")
        return self.registry.execute(identity, request)

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
            reservation_id = self._extract(resolved_text=normalized, pattern=r"(?:reservation|booking)\s*#?([a-z0-9-]+)")
            if reservation_id:
                return CommandRequest("GET_RESERVATION", {"reservation_id": reservation_id})
        room = self._extract(text, r"room\s*(\d+)")
        if room and any(word in normalized for word in ("status", "ready", "dirty", "cleaning", "available")):
            return CommandRequest("GET_ROOM_STATUS", {"room_number": room})
        if room and any(phrase in normalized for phrase in ("mark", "clean")):
            return CommandRequest("MARK_ROOM_CLEAN", {"room_number": room})
        if "incident" in normalized or "broken" in normalized or "not working" in normalized:
            incident_type = "HOUSEKEEPING" if "clean" in normalized or "housekeeping" in normalized else "MAINTENANCE"
            description = text
            return CommandRequest("CREATE_INCIDENT", {"room_number": room, "incident_type": incident_type, "description": description})
        if "open incidents" in normalized or "incidents" in normalized:
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
                    return candidate
        return None
