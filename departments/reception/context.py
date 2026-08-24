from __future__ import annotations

from typing import Any

from departments.base import Shift


SHIFT_CONTEXT: dict[Shift, dict[str, Any]] = {
    Shift.MORNING: {
        "shift_name": "Morning",
        "focus": ["arrivals", "room readiness"],
        "suggested_prompts": [
            "today's arrivals",
            "which rooms are not ready?",
        ],
        "system_prompt_hint": "Focus on arrivals, room readiness, and front-desk operational issues.",
    },
    Shift.AFTERNOON: {
        "shift_name": "Afternoon",
        "focus": ["departures", "incidents"],
        "suggested_prompts": [
            "who is leaving today?",
            "show open incidents",
        ],
        "system_prompt_hint": "Focus on departures, incidents, and the remaining day's operations.",
    },
    Shift.NIGHT: {
        "shift_name": "Night",
        "focus": ["audit", "next-day preparation"],
        "suggested_prompts": [
            "give me today's summary",
            "list automations",
        ],
        "system_prompt_hint": "Focus on operational review, audit-related checks, and next-day preparation.",
    },
}


def get_shift_context(shift: str | Shift) -> dict[str, Any]:
    """Return immutable-source shift hints as a fresh dictionary."""
    parsed = Shift.parse(shift)
    source = SHIFT_CONTEXT[parsed]
    return {
        **source,
        "focus": list(source["focus"]),
        "suggested_prompts": list(source["suggested_prompts"]),
    }
