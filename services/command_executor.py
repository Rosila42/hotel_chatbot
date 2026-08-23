from __future__ import annotations

from datetime import date
from typing import Any, Callable

from sqlalchemy.orm import Session

from core.permissions import Identity
from models.commands import CommandDefinition, CommandRequest, CommandResult, ResultKind
from services.audit_service import AuditEvent, AuditService
from services.automation_service import (
    AutomationExecutionError,
    AutomationService,
)
from services.faq_service import FAQService
from services.pms_service import PMSService
from services.response_formatter import ResponseFormatter


class CommandExecutor:
    """Execute already-authorized, structurally validated commands."""

    def __init__(
        self,
        pms: PMSService,
        automation: AutomationService | None = None,
        faq: FAQService | None = None,
        audit: AuditService | None = None,
        formatter: ResponseFormatter | None = None,
        help_provider: Callable[[Identity], list[str]] | None = None,
    ) -> None:
        self.pms = pms
        self.automation = automation
        self.faq = faq or FAQService()
        self.audit = audit or AuditService()
        self.formatter = formatter or ResponseFormatter()
        self.help_provider = help_provider

    def execute(
        self,
        identity: Identity,
        request: CommandRequest,
        command: CommandDefinition,
        *,
        db: Session | None = None,
    ) -> CommandResult:
        try:
            result_data = self._dispatch(identity, command.name, request.parameters)
            result = CommandResult(
                ResultKind.SUCCESS,
                self.formatter.format(command.name, result_data),
                result_data,
                command.name,
            )
            self._audit(identity, request, command, result, db=db)
            return result
        except AutomationExecutionError as exc:
            result = CommandResult(
                ResultKind.FAILED,
                "The automation could not be completed.",
                getattr(exc, "details", None),
                command.name,
            )
            self._audit(identity, request, command, result, details=getattr(exc, "details", str(exc)), db=db)
            return result
        except (ValueError, KeyError) as exc:
            result = CommandResult(ResultKind.INVALID_PARAMS, str(exc), command=command.name)
            self._audit(identity, request, command, result, details=str(exc), db=db)
            return result
        except (TimeoutError, ConnectionError) as exc:
            result = CommandResult(
                ResultKind.FAILED,
                "The PMS is temporarily unavailable. Please try again.",
                command=command.name,
            )
            self._audit(identity, request, command, result, details=str(exc), db=db)
            return result
        except Exception:
            result = CommandResult(
                ResultKind.FAILED,
                "The requested operation could not be completed.",
                command=command.name,
            )
            self._audit(identity, request, command, result, details="internal_error", db=db)
            return result

    def _audit(
        self,
        identity: Identity,
        request: CommandRequest,
        command: CommandDefinition,
        result: CommandResult,
        *,
        details: Any = None,
        db: Session | None = None,
    ) -> None:
        self.audit.record(
            AuditEvent(
                identity=identity,
                command=command.name,
                operation_type=command.operation_type.value,
                result_kind=result.kind,
                parameters=request.parameters,
                details=details,
            ),
            db=db,
        )

    def _dispatch(self, identity: Identity, name: str, params: dict[str, Any]) -> Any:
        if name == "HELP":
            return self.help_provider(identity) if self.help_provider else []
        if name == "GET_SYSTEM_STATUS":
            return {
                "pms": "available",
                "chatbot": "available",
                "ai": "configured" if False else "optional",
                "automation": "configured" if self.automation else "not configured",
            }
        if name == "SEARCH_GUEST":
            return self.pms.search_guest(self._required_text(params, "name"))
        if name == "GET_RESERVATION":
            return self.pms.get_reservation(params.get("reservation_id"), params.get("guest_name"))
        if name == "GET_ARRIVALS":
            return self.pms.get_arrivals(self._parse_date(params.get("date")))
        if name == "GET_DEPARTURES":
            return self.pms.get_departures(self._parse_date(params.get("date")))
        if name == "GET_ROOM_STATUS":
            return self.pms.get_room_status(params.get("room_number"), params.get("filter"))
        if name == "MARK_ROOM_CLEAN":
            return self.pms.mark_room_clean(self._required_text(params, "room_number"))
        if name == "GET_INCIDENTS":
            return self.pms.get_incidents(params.get("status"), params.get("room_number"))
        if name == "CREATE_INCIDENT":
            return self.pms.create_incident(
                params.get("room_number"),
                self._required_text(params, "incident_type"),
                self._required_text(params, "description"),
            )
        if name == "RESOLVE_INCIDENT":
            return self.pms.resolve_incident(self._required_text(params, "incident_id"))
        if name == "GET_OPERATIONAL_SUMMARY":
            return self.pms.get_operational_summary(
                self._parse_date(params.get("date")) if params.get("date") else None
            )
        if name == "FAQ_SEARCH":
            return self.faq.search(self._required_text(params, "query"))
        if not self.automation:
            raise RuntimeError("Automation service is not configured")
        if name == "LIST_AUTOMATIONS":
            return self.automation.list_automations()
        automation_id = self._required_text(params, "automation_id")
        if name == "ENABLE_AUTOMATION":
            return self.automation.enable(automation_id)
        if name == "DISABLE_AUTOMATION":
            return self.automation.disable(automation_id)
        if name == "RUN_AUTOMATION":
            return self.automation.run(automation_id)
        if name == "GET_AUTOMATION_STATUS":
            return self.automation.status(automation_id)
        if name == "GET_AUTOMATION_HISTORY":
            return self.automation.history(automation_id)
        raise KeyError(name)

    @staticmethod
    def _required_text(params: dict[str, Any], key: str) -> str:
        value = params.get(key)
        if value is None or not str(value).strip():
            raise ValueError(f"Missing required parameter: {key}")
        return str(value).strip()

    @staticmethod
    def _parse_date(value: Any) -> date:
        if value in (None, "", "today"):
            return date.today()
        if isinstance(value, date):
            return value
        return date.fromisoformat(str(value))
