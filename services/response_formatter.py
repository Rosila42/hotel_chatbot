from __future__ import annotations

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

        if isinstance(result_data, list):
            return f"Found {len(result_data)} result(s)."

        return str(result_data)
