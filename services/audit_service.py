from __future__ import annotations

import json
from typing import Any

from core.permissions import Identity
from storage import AuditRecord, SessionLocal


class AuditService:
    """Persist a compact audit trail for chatbot-triggered operations."""

    @staticmethod
    def record(
        identity: Identity,
        command: str,
        operation_type: str,
        success: bool,
        *,
        parameters: dict[str, Any] | None = None,
        details: Any = None,
    ) -> None:
        safe_parameters = AuditService._sanitize(parameters or {})
        safe_details = AuditService._sanitize(details)
        with SessionLocal() as db:
            db.add(
                AuditRecord(
                    user_id=identity.user_id,
                    role=identity.role,
                    department=identity.department,
                    command=command,
                    operation_type=operation_type,
                    success=success,
                    parameters=json.dumps(safe_parameters, default=str),
                    details=json.dumps(safe_details, default=str),
                )
            )
            db.commit()

    @staticmethod
    def record_system(command: str, operation_type: str, success: bool, *, details: Any = None) -> None:
        AuditService.record(
            Identity("system", "system", "system"),
            command,
            operation_type,
            success,
            details=details,
        )

    @staticmethod
    def _sanitize(value: Any) -> Any:
        if isinstance(value, dict):
            hidden = {"password", "passwd", "token", "authorization", "credit_card", "card_number", "cvv", "passport", "id_number"}
            return {
                key: "[REDACTED]" if key.lower() in hidden else AuditService._sanitize(item)
                for key, item in value.items()
            }
        if isinstance(value, (list, tuple)):
            return [AuditService._sanitize(item) for item in value]
        if hasattr(value, "__dict__"):
            return str(value)
        return value
