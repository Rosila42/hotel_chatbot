from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Callable, Protocol

from models.commands import CommandRequest


class Parser(Protocol):
    """Contract between natural-language interpretation and the deterministic core.

    A parser may use rules, an LLM, or another interpretation mechanism, but it may
    only translate text into a CommandRequest (or return None). It must not perform
    authorization, confirmation, service calls, or PMS operations.
    """

    def parse(self, text: str) -> CommandRequest | None:
        ...


class DeterministicParser:
    """Rule-based parser implementing the Phase 2 parser contract."""

    def __init__(self, today_provider: Callable[[], date] = date.today) -> None:
        self._today_provider = today_provider

    def parse(self, text: str) -> CommandRequest | None:
        normalized = " ".join(text.strip().lower().split())
        if not normalized:
            return None

        if normalized in {"help", "what can you do", "what can you help with", "commands"}:
            return CommandRequest("HELP")
        if normalized in {"status", "system status", "what is the system status", "is the system up"}:
            return CommandRequest("GET_SYSTEM_STATUS")

        automation_id = self._automation_id(normalized)
        if automation_id:
            if self._has_any(normalized, "list", "show", "available") and "automation" in normalized:
                return CommandRequest("LIST_AUTOMATIONS")
            if self._has_any(normalized, "enable", "activate", "turn on"):
                return CommandRequest("ENABLE_AUTOMATION", {"automation_id": automation_id})
            if self._has_any(normalized, "disable", "deactivate", "turn off"):
                return CommandRequest("DISABLE_AUTOMATION", {"automation_id": automation_id})
            if self._has_any(normalized, "run", "execute", "start"):
                return CommandRequest("RUN_AUTOMATION", {"automation_id": automation_id})
            if "history" in normalized:
                return CommandRequest("GET_AUTOMATION_HISTORY", {"automation_id": automation_id})
            if "status" in normalized:
                return CommandRequest("GET_AUTOMATION_STATUS", {"automation_id": automation_id})

        generic_automation_id = self._extract_automation_id(text)
        if generic_automation_id:
            if self._has_any(normalized, "enable", "activate", "turn on"):
                return CommandRequest("ENABLE_AUTOMATION", {"automation_id": generic_automation_id})
            if self._has_any(normalized, "disable", "deactivate", "turn off"):
                return CommandRequest("DISABLE_AUTOMATION", {"automation_id": generic_automation_id})
            if self._has_any(normalized, "run", "execute", "start"):
                return CommandRequest("RUN_AUTOMATION", {"automation_id": generic_automation_id})
            if "history" in normalized:
                return CommandRequest("GET_AUTOMATION_HISTORY", {"automation_id": generic_automation_id})
            if "status" in normalized:
                return CommandRequest("GET_AUTOMATION_STATUS", {"automation_id": generic_automation_id})

        if "automation" in normalized and self._has_any(normalized, "list", "show", "available"):
            return CommandRequest("LIST_AUTOMATIONS")

        if "incidents" in normalized and self._has_any(normalized, "list", "show", "view", "get", "open"):
            status = "OPEN" if self._has_any(normalized, "open", "unresolved", "active") else None
            params = {"status": status} if status else {}
            room = self._extract_room_number(text)
            if room:
                params["room_number"] = room
            return CommandRequest("GET_INCIDENTS", params)

        incident_id = self._extract_incident_id(text)
        if incident_id and self._has_any(normalized, "resolve incident", "close incident", "resolve issue", "close issue"):
            return CommandRequest("RESOLVE_INCIDENT", {"incident_id": incident_id})

        # Room-readiness questions must take precedence over generic arrival wording.
        if self._has_any(normalized, "not ready", "not-ready", "aren't ready", "isn't ready"):
            filter_name = "not_ready_arrivals" if "arrival" in normalized else "not_ready"
            return CommandRequest("GET_ROOM_STATUS", {"filter": filter_name})

        if self._has_any(normalized, "dirty rooms", "cleaning rooms", "available rooms"):
            if "dirty rooms" in normalized:
                filter_name = "dirty"
            elif "cleaning rooms" in normalized:
                filter_name = "cleaning"
            else:
                filter_name = "available"
            return CommandRequest("GET_ROOM_STATUS", {"filter": filter_name})

        if self._mentions_arrivals(normalized):
            return CommandRequest("GET_ARRIVALS", {"date": self._requested_date(normalized).isoformat()})
        if self._mentions_departures(normalized):
            return CommandRequest("GET_DEPARTURES", {"date": self._requested_date(normalized).isoformat()})

        if self._mentions_guest_search(normalized):
            name = self._extract_guest_name(text)
            if name:
                return CommandRequest("SEARCH_GUEST", {"name": name})

        if "reservation" in normalized or "booking" in normalized:
            reservation_id = self._extract(
                text,
                r"(?:reservation|booking)\s*(?:number|no\.?|id)?\s*#?([a-z0-9-]+)",
            )
            if reservation_id and reservation_id.casefold() not in {"for", "status", "details", "today", "tomorrow"}:
                return CommandRequest("GET_RESERVATION", {"reservation_id": reservation_id})
            guest_name = self._extract_guest_name(text)
            if guest_name and self._has_any(normalized, "reservation", "booking"):
                return CommandRequest("GET_RESERVATION", {"guest_name": guest_name})

        room = self._extract_room_number(text)

        if self._mentions_incident_creation(normalized):
            incident_type = (
                "HOUSEKEEPING"
                if self._has_any(normalized, "housekeeping", "cleaning", "dirty", "linen", "towel")
                else "MAINTENANCE"
            )
            return CommandRequest(
                "CREATE_INCIDENT",
                {
                    "room_number": room,
                    "incident_type": incident_type,
                    "description": text,
                },
            )

        if room and (
            self._has_any(normalized, "mark clean", "marked clean", "set clean", "make clean", "clean room")
            or ("clean" in normalized and self._has_any(normalized, "mark", "set", "make"))
        ):
            return CommandRequest("MARK_ROOM_CLEAN", {"room_number": room})

        if room and self._has_any(
            normalized,
            "status",
            "ready",
            "dirty",
            "clean",
            "cleaning",
            "available",
            "occupied",
            "vacant",
            "out of order",
        ):
            return CommandRequest("GET_ROOM_STATUS", {"room_number": room})

        if self._has_any(
            normalized,
            "operational summary",
            "hotel summary",
            "daily summary",
            "daily ops",
            "operations summary",
            "today's summary",
        ):
            return CommandRequest("GET_OPERATIONAL_SUMMARY", {"date": self._requested_date(normalized).isoformat()})

        if self._mentions_faq(normalized):
            return CommandRequest("FAQ_SEARCH", {"query": text})

        return None

    @staticmethod
    def _has_any(text: str, *phrases: str) -> bool:
        return any(phrase in text for phrase in phrases)

    @staticmethod
    def _mentions_arrivals(text: str) -> bool:
        return any(phrase in text for phrase in (
            "arrival", "arrivals", "arriving", "check in", "checking in",
            "check-ins", "check ins", "expected guests",
        ))

    @staticmethod
    def _mentions_departures(text: str) -> bool:
        return any(phrase in text for phrase in (
            "departure", "departures", "leaving", "who is leaving", "check out",
            "checking out", "check-outs", "check outs", "leaving guests",
        ))

    @staticmethod
    def _mentions_guest_search(text: str) -> bool:
        return any(phrase in text for phrase in (
            "search guest", "find guest", "look up guest", "lookup guest",
            "search for guest", "find the guest", "look up the guest",
        )) or bool(re.search(r"^(?:find|search|lookup|look up)\s+[A-Za-z]", text))

    @staticmethod
    def _mentions_incident_creation(text: str) -> bool:
        return any(phrase in text for phrase in (
            "create incident", "report incident", "report a problem", "report an issue",
            "report a dirty room", "report dirty room", "broken", "not working", "isn't working",
            "is not working", "doesn't work", "does not work", "malfunction", "problem with", "issue with",
            "problem", "issue",
        ))

    @staticmethod
    def _mentions_faq(text: str) -> bool:
        return any(phrase in text for phrase in (
            "breakfast", "checkout time", "check-out time", "check out time",
            "what time is checkout", "when is checkout", "check-in time", "check in time",
            "wifi", "wi-fi", "internet", "hotel policy", "cancellation policy", "parking",
        ))

    def _requested_date(self, text: str) -> date:
        today = self._today_provider()
        if "tomorrow" in text:
            return today + timedelta(days=1)
        if "yesterday" in text:
            return today - timedelta(days=1)
        match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", text)
        if match:
            try:
                return date.fromisoformat(match.group(1))
            except ValueError:
                pass
        return today

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
    def _extract_room_number(text: str) -> str | None:
        return DeterministicParser._extract(text, r"\broom\s*(?:number\s*)?#?([0-9]+)\b")

    @staticmethod
    def _extract_incident_id(text: str) -> str | None:
        return DeterministicParser._extract(text, r"(?:incident|issue|ticket)\s*(?:number|no\.?|id)?\s*#?([a-z0-9-]+)")

    @staticmethod
    def _extract_automation_id(text: str) -> str | None:
        return DeterministicParser._extract(text, r"(?:automation|workflow)\s*(?:id)?\s*[:#-]?\s*([A-Za-z0-9_-]+)")

    @staticmethod
    def _extract_guest_name(text: str) -> str | None:
        patterns = (
            r"(?:search|find|lookup|look up)\s+(?:for\s+)?(?:the\s+)?guest\s+(?:called\s+|named\s+)?(.+)$",
            r"(?:search|find|lookup|look up)\s+(?:for\s+)?(.+)$",
            r"(?:guest|reservation|booking)\s+(?:for|of)\s+(.+)$",
        )
        for pattern in patterns:
            match = re.search(pattern, text.strip(), re.IGNORECASE)
            if match:
                candidate = match.group(1).strip(" :,#")
                if candidate:
                    return candidate
        return None
