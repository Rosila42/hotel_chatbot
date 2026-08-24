from __future__ import annotations

from departments.base import DepartmentContext


class HousekeepingChat:
    department = "housekeeping"
    suggested_prompts = (
        "which rooms are not ready?",
        "show open incidents",
    )

    def __init__(self) -> None:
        self.context = DepartmentContext(self.department)

    def can_mark_room_clean(self) -> bool:
        return True

    def get_context(self) -> dict[str, object]:
        return {
            "department": self.context.department,
            "shift": None,
            "suggested_prompts": list(self.suggested_prompts),
        }
