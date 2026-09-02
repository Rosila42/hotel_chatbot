from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from enum import Enum
from typing import Any


class ResponseFormatter:
    """Convert successful command data into concise user-facing text."""

    @staticmethod
    def format(command: str, result_data: Any) -> str:
        if command == "HELP":
            names = result_data or []
            return "Available commands: " + ", ".join(names)

        if command == "GET_SYSTEM_STATUS":
            return "; ".join(f"{key}: {value}" for key, value in result_data.items())

        if command == "FAQ_SEARCH":
            matches = result_data.get("matches", [])
            if not matches:
                return "I couldn't find an answer in the approved FAQ content."
            return matches[0]["answer"]

        if command in {"GET_ARRIVALS", "GET_DEPARTURES"}:
            label = "arrivals" if command == "GET_ARRIVALS" else "departures"
            if not result_data:
                return f"No {label} found."
            return f"{label.capitalize()} ({len(result_data)}):\n" + "\n".join(
                f"• {item.guest_name} — room {item.room_number} — {item.status} "
                f"(reservation {item.reservation_id}; {item.arrival} → {item.departure})"
                for item in result_data
            )

        if command == "SEARCH_GUEST":
            if not result_data:
                return "No guests found."
            return f"Guests ({len(result_data)}):\n" + "\n".join(
                f"• {guest.name} (guest {guest.guest_id})" for guest in result_data
            )

        if command == "GET_RESERVATION":
            if not result_data:
                return "No reservations found."
            return f"Reservations ({len(result_data)}):\n" + "\n".join(
                f"• {reservation.reservation_id} — {reservation.guest_name} — room {reservation.room_number} — "
                f"{reservation.status} — {reservation.arrival} → {reservation.departure}"
                for reservation in result_data
            )

        if command == "GET_ROOM_STATUS":
            if not result_data:
                return "No matching rooms found."
            return f"Rooms ({len(result_data)}):\n" + "\n".join(
                f"• Room {room.room_number} — {room.status.value} — {room.room_type}"
                for room in result_data
            )

        if command == "GET_INCIDENTS":
            if not result_data:
                return "No matching incidents found."
            return f"Incidents ({len(result_data)}):\n" + "\n".join(
                f"• {incident.incident_id} — room {incident.room_number or 'N/A'} — "
                f"{incident.incident_type} — {incident.status.value} — {incident.description}"
                for incident in result_data
            )

        if command == "CREATE_INCIDENT":
            return (
                f"Incident created: {result_data.incident_id} — "
                f"room {result_data.room_number or 'N/A'} — {result_data.incident_type} — "
                f"{result_data.description} — {result_data.status.value}"
            )

        if command == "MARK_ROOM_CLEAN":
            return f"Room {result_data.room_number} is now {result_data.status.value}."

        if command == "GET_OPERATIONAL_SUMMARY":
            return (
                "Operational summary:\n"
                f"• Arrivals: {result_data.arrivals}\n"
                f"• Departures: {result_data.departures}\n"
                f"• Occupancy: {result_data.occupancy_rate:.1f}%\n"
                f"• Available rooms: {result_data.available_rooms}\n"
                f"• Rooms requiring attention: {result_data.rooms_requiring_attention}\n"
                f"• Open incidents: {result_data.open_incidents}"
            )

        if command in {"LIST_AUTOMATIONS", "GET_AUTOMATION_STATUS", "ENABLE_AUTOMATION", "DISABLE_AUTOMATION"}:
            if command == "LIST_AUTOMATIONS":
                if not result_data:
                    return "No automations configured."
                return f"Automations ({len(result_data)}):\n" + "\n".join(
                    f"• {item['id']} — {item['name']} — "
                    f"{'enabled' if item['enabled'] else 'disabled'} — {item['description']}"
                    for item in result_data
                )
            return (
                f"Automation {result_data['id']} — {result_data['name']} — "
                f"{'enabled' if result_data['enabled'] else 'disabled'} — "
                f"schedule: {result_data.get('schedule') or 'none'}"
            )

        if command == "RUN_AUTOMATION":
            rooms = result_data.get("rooms_requiring_attention", [])
            room_text = ", ".join(str(room) for room in rooms) if rooms else "none"
            return (
                f"Automation {result_data.get('automation_id')} — {result_data.get('status')}. "
                f"Rooms requiring attention: {room_text}."
            )

        if command == "GET_AUTOMATION_HISTORY":
            if not result_data:
                return "No automation execution history found."
            lines = []
            for item in result_data:
                details = item.get("details")
                if isinstance(details, str):
                    details = details.strip()
                if isinstance(details, Mapping):
                    details = ", ".join(f"{key}={value}" for key, value in details.items())
                lines.append(
                    f"• {item['created_at']} — {item['status']} — {details or 'no details'}"
                )
            return f"Automation history ({len(result_data)}):\n" + "\n".join(lines)

        return ResponseFormatter._format_generic(result_data)

    @staticmethod
    def _format_generic(result_data: Any) -> str:
        if result_data is None:
            return "Operation completed."
        if is_dataclass(result_data):
            return ResponseFormatter._format_mapping(asdict(result_data))
        if isinstance(result_data, Mapping):
            return ResponseFormatter._format_mapping(result_data)
        if isinstance(result_data, Sequence) and not isinstance(result_data, (str, bytes, bytearray)):
            if not result_data:
                return "No results found."
            return "Results:\n" + "\n".join(
                f"• {ResponseFormatter._to_text(item)}" for item in result_data
            )
        return ResponseFormatter._to_text(result_data)

    @staticmethod
    def _format_mapping(data: Mapping[str, Any]) -> str:
        return "\n".join(f"• {key}: {ResponseFormatter._to_text(value)}" for key, value in data.items())

    @staticmethod
    def _to_text(value: Any) -> str:
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        if is_dataclass(value):
            return ResponseFormatter._format_mapping(asdict(value))
        if isinstance(value, Mapping):
            return ", ".join(f"{key}={ResponseFormatter._to_text(item)}" for key, item in value.items())
        if isinstance(value, (list, tuple, set)):
            return ", ".join(ResponseFormatter._to_text(item) for item in value)
        return str(value)
