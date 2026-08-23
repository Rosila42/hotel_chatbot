from __future__ import annotations

import re
from datetime import date
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
    """Rule-based parser implementing the Phase 2 parser contract.

    This class owns natural-language interpretation only. The router remains the
    single trusted policy gate for authorization, validation, confirmation, and
    execution.
    """

    def __init__(self, today_provider: Callable[[], date] = date.today) -> None:
        # Injecting the date source keeps parser tests deterministic without changing
        # the production behavior, which still uses the host application's current date.
        self._today_provider = today_provider

    def parse(self, text: str) -> CommandRequest | None:
        normalized = text.strip().lower()
        if not normalized:
            return None

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

        # Check the explicit incidents-list intent before the generic incident/create
        # intent so "show incidents" cannot accidentally become CREATE_INCIDENT.
        if "incidents" in normalized and any(
            word in normalized for word in ("list", "show", "open", "view", "get")
        ):
            return CommandRequest("GET_INCIDENTS", {"status": "OPEN"})

        if "arrival" in normalized or "checking in" in normalized:
            return CommandRequest(
                "GET_ARRIVALS",
                {"date": self._today_provider().isoformat()},
            )
        if "departure" in normalized or "checking out" in normalized:
            return CommandRequest(
                "GET_DEPARTURES",
                {"date": self._today_provider().isoformat()},
            )
        if "guest" in normalized and any(word in normalized for word in ("find", "search", "look up", "lookup")):
            name = self._after_keyword(text, ("guest", "for"))
            if name:
                return CommandRequest("SEARCH_GUEST", {"name": name})
        if "reservation" in normalized:
            reservation_id = self._extract(
                normalized,
                r"(?:reservation|booking)\s*#?([a-z0-9-]+)",
            )
            if reservation_id and reservation_id.lower() not in {"for", "status"}:
                return CommandRequest(
                    "GET_RESERVATION",
                    {"reservation_id": reservation_id},
                )

        room = self._extract(text, r"room\s*(\d+)")
        if room and "mark" in normalized and "clean" in normalized:
            return CommandRequest("MARK_ROOM_CLEAN", {"room_number": room})
        if room and any(
            word in normalized
            for word in ("status", "ready", "dirty", "cleaning", "available")
        ):
            return CommandRequest("GET_ROOM_STATUS", {"room_number": room})
        if "incident" in normalized or "broken" in normalized or "not working" in normalized:
            incident_type = (
                "HOUSEKEEPING"
                if "clean" in normalized or "housekeeping" in normalized
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
        if "operational summary" in normalized or "hotel summary" in normalized or "daily summary" in normalized:
            return CommandRequest("GET_OPERATIONAL_SUMMARY")
        if any(
            word in normalized
            for word in ("breakfast", "checkout time", "check-out time", "policy", "wifi", "wi-fi")
        ):
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
