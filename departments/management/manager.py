from __future__ import annotations

from departments.base import DepartmentContext


class ManagementChat:
    department = "management"
    suggested_prompts = (
        "operational summary",
        "list automations",
        "show automation NIGHT_AUDIT status",
    )

    def __init__(self) -> None:
        self.context = DepartmentContext(self.department)

    def can_view_operational_summary(self) -> bool:
        return True

    def get_context(self) -> dict[str, object]:
        return {
            "department": self.context.department,
            "shift": None,
            "suggested_prompts": list(self.suggested_prompts),
        }
