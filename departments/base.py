from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Shift(str, Enum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    NIGHT = "night"

    @classmethod
    def parse(cls, value: str | Shift) -> Shift:
        if isinstance(value, cls):
            return value
        normalized = str(value).strip().lower()
        try:
            return cls(normalized)
        except ValueError as exc:
            raise ValueError(f"Unsupported shift: {value}") from exc


@dataclass(frozen=True)
class DepartmentContext:
    department: str
    shift: Shift | None = None

    def __post_init__(self) -> None:
        department = self.department.strip().lower()
        if not department:
            raise ValueError("Department cannot be empty")
        object.__setattr__(self, "department", department)
        if self.shift is not None:
            object.__setattr__(self, "shift", Shift.parse(self.shift))
