from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from hotel_chatbot_v2.services.pms_service import PMSService


@dataclass(frozen=True)
class AutomationTemplate:
    automation_id: str
    name: str
    description: str


TEMPLATES = {
    "MORNING_ARRIVAL_CHECK": AutomationTemplate(
        "MORNING_ARRIVAL_CHECK",
        "Morning Arrival Check",
        "Identify today's arrival rooms that are not ready.",
    ),
}


class AutomationService:
    """Manages predefined automation templates; execution is intentionally separate."""

    def __init__(self, pms: PMSService) -> None:
        self.pms = pms
        self.enabled: set[str] = set()

    def list_automations(self) -> list[dict[str, Any]]:
        return [
            {
                "id": template.automation_id,
                "name": template.name,
                "description": template.description,
                "enabled": template.automation_id in self.enabled,
            }
            for template in TEMPLATES.values()
        ]

    def enable(self, automation_id: str) -> dict[str, Any]:
        self._require_template(automation_id)
        self.enabled.add(automation_id)
        return self._status(automation_id)

    def disable(self, automation_id: str) -> dict[str, Any]:
        self._require_template(automation_id)
        self.enabled.discard(automation_id)
        return self._status(automation_id)

    def status(self, automation_id: str) -> dict[str, Any]:
        self._require_template(automation_id)
        return self._status(automation_id)

    def run(self, automation_id: str) -> dict[str, Any]:
        self._require_template(automation_id)
        if automation_id == "MORNING_ARRIVAL_CHECK":
            rooms = self.pms.get_room_status(filter_name="not_ready_arrivals")
            return {
                "automation_id": automation_id,
                "status": "COMPLETED",
                "rooms_requiring_attention": [room.room_number for room in rooms],
            }
        raise ValueError(f"Automation {automation_id} is not implemented")

    def _require_template(self, automation_id: str) -> None:
        if automation_id not in TEMPLATES:
            raise ValueError(f"Unknown automation: {automation_id}")

    def _status(self, automation_id: str) -> dict[str, Any]:
        template = TEMPLATES[automation_id]
        return {
            "id": template.automation_id,
            "name": template.name,
            "enabled": automation_id in self.enabled,
        }
