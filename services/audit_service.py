from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from core.permissions import Identity
from models.commands import ResultKind
from storage import AuditRecord, SessionLocal


@dataclass(frozen=True)
class AuditEvent:
    identity: Identity
    command: str
    operation_type: str
    result_kind: ResultKind
    parameters: dict[str, Any] | None = None
    details: Any = None


class AuditService:
    """Persist a compact audit trail for chatbot-triggered operations."""

    @staticmethod
    def record(event: AuditEvent) -> None:
        safe_parameters = AuditService._sanitize(event.parameters or {})
        safe_details = AuditService._sanitize(event.details)
        with SessionLocal() as db:
            db.add(
                AuditRecord(
                    user_id=event.identity.user_id,
                    role=event.identity.role,
                    department=event.identity.department,
                    command=event.command,
                    operation_type=event.operation_type,
                    success=event.result_kind is ResultKind.SUCCESS,
                    parameters=json.dumps(safe_parameters, default=str),
                    details=json.dumps(
                        {"result_kind": event.result_kind.value, "details": safe_details},
                        default=str,
                    ),
                )
            )
            db.commit()

    @staticmethod
    def record_system(
        command: str,
        operation_type: str,
        result_kind: ResultKind,
        *,
        details: Any = None,
    ) -> None:
        AuditService.record(
            AuditEvent(
                identity=Identity("system", "system", "system"),
                command=command,
                operation_type=operation_type,
                result_kind=result_kind,
                details=details,
            )
        )

    @staticmethod
    def _sanitize(value: Any) -> Any:
        if isinstance(value, dict):
            hidden = {
                "password",
                "passwd",
                "token",
                "authorization",
                "credit_card",
                "card_number",
                "cvv",
                "passport",
                "id_number",
            }
            return {
                key: "[REDACTED]" if key.lower() in hidden else AuditService._sanitize(item)
                for key, item in value.items()
            }
        if isinstance(value, (list, tuple)):
            return [AuditService._sanitize(item) for item in value]
        if hasattr(value, "__dict__"):
            return str(value)
        return value
