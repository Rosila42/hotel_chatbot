from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReceptionContext:
    shift: str


class ReceptionChat:
    VALID_SHIFTS = {"morning", "afternoon", "night"}

    def __init__(self, shift: str) -> None:
        normalized = shift.lower()
        if normalized not in self.VALID_SHIFTS:
            raise ValueError(f"Unsupported reception shift: {shift}")
        self.context = ReceptionContext(normalized)
