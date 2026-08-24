from __future__ import annotations

from dataclasses import dataclass

from departments.base import DepartmentContext, Shift
from departments.reception.context import get_shift_context


@dataclass(frozen=True)
class ReceptionContext:
    shift: Shift


class ReceptionChat:
    """Department context for Reception without duplicating commands by shift."""

    department = "reception"

    def __init__(self, shift: str | Shift) -> None:
        self.context = ReceptionContext(Shift.parse(shift))

    @property
    def department_context(self) -> DepartmentContext:
        return DepartmentContext(self.department, self.context.shift)

    @property
    def shift(self) -> str:
        return self.context.shift.value

    def get_context(self) -> dict:
        return dict(get_shift_context(self.shift))
