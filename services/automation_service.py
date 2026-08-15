from __future__ import annotations

from dataclasses import dataclass
from json import dumps
from typing import Any

from services.pms_service import PMSService
from storage import AutomationDefinitionRecord, AutomationExecutionRecord, SessionLocal


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
    def __init__(self, pms: PMSService) -> None:
        self.pms = pms
        self._ensure_definitions()

    def _ensure_definitions(self) -> None:
        with SessionLocal() as db:
            for automation_id in TEMPLATES:
                if db.get(AutomationDefinitionRecord, automation_id) is None:
                    db.add(AutomationDefinitionRecord(automation_id=automation_id, enabled=False))
            db.commit()

    def list_automations(self) -> list[dict[str, Any]]:
        with SessionLocal() as db:
            records = {r.automation_id: r for r in db.query(AutomationDefinitionRecord).all()}
        return [{
            "id": t.automation_id,
            "name": t.name,
            "description": t.description,
            "enabled": bool(records[t.automation_id].enabled),
        } for t in TEMPLATES.values()]

    def enable(self, automation_id: str) -> dict[str, Any]:
        record = self._record(automation_id)
        record.enabled = True
        return self._save_status(record)

    def disable(self, automation_id: str) -> dict[str, Any]:
        record = self._record(automation_id)
        record.enabled = False
        return self._save_status(record)

    def status(self, automation_id: str) -> dict[str, Any]:
        return self._status(self._record(automation_id))

    def run(self, automation_id: str) -> dict[str, Any]:
        self._record(automation_id)
        if automation_id != "MORNING_ARRIVAL_CHECK":
            raise ValueError(f"Automation {automation_id} is not implemented")
        try:
            rooms = self.pms.get_room_status(filter_name="not_ready_arrivals")
            result = {"automation_id": automation_id, "status": "COMPLETED", "rooms_requiring_attention": [r.room_number for r in rooms]}
            self._record_execution(automation_id, "COMPLETED", result)
            return result
        except Exception as exc:
            result = {"automation_id": automation_id, "status": "FAILED", "error": str(exc)}
            self._record_execution(automation_id, "FAILED", result)
            return result

    def history(self, automation_id: str) -> list[dict[str, Any]]:
        self._record(automation_id)
        with SessionLocal() as db:
            rows = db.query(AutomationExecutionRecord).filter(
                AutomationExecutionRecord.automation_id == automation_id
            ).order_by(AutomationExecutionRecord.created_at.desc()).limit(50).all()
        return [{"id": r.id, "automation_id": r.automation_id, "status": r.status, "details": r.details, "created_at": r.created_at.isoformat()} for r in rows]

    def _record(self, automation_id: str) -> AutomationDefinitionRecord:
        if automation_id not in TEMPLATES:
            raise ValueError(f"Unknown automation: {automation_id}")
        with SessionLocal() as db:
            record = db.get(AutomationDefinitionRecord, automation_id)
            if record is None:
                record = AutomationDefinitionRecord(automation_id=automation_id, enabled=False)
                db.add(record)
                db.commit()
                db.refresh(record)
            return AutomationDefinitionRecord(automation_id=record.automation_id, enabled=record.enabled, schedule=record.schedule)

    def _save_status(self, source: AutomationDefinitionRecord) -> dict[str, Any]:
        with SessionLocal() as db:
            record = db.get(AutomationDefinitionRecord, source.automation_id)
            if record is None:
                record = AutomationDefinitionRecord(automation_id=source.automation_id, enabled=source.enabled)
                db.add(record)
            else:
                record.enabled = source.enabled
            db.commit()
            db.refresh(record)
            return self._status(record)

    @staticmethod
    def _status(record: AutomationDefinitionRecord) -> dict[str, Any]:
        template = TEMPLATES[record.automation_id]
        return {"id": template.automation_id, "name": template.name, "description": template.description, "enabled": bool(record.enabled), "schedule": record.schedule}

    @staticmethod
    def _record_execution(automation_id: str, status: str, result: dict[str, Any]) -> None:
        with SessionLocal() as db:
            db.add(AutomationExecutionRecord(automation_id=automation_id, status=status, details=dumps(result)))
            db.commit()
