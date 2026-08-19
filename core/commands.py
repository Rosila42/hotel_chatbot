from __future__ import annotations

from datetime import date
from typing import Any

from models.commands import (
    CommandDefinition,
    CommandRequest,
    CommandResult,
    ConfirmationPolicy,
    OperationType,
)
from core.permissions import Identity, PermissionService
from services.audit_service import AuditService
from services.automation_service import AutomationService
from services.faq_service import FAQService
from services.pms_service import PMSService


class CommandRegistry:
    def __init__(
        self,
        pms: PMSService,
        permissions: PermissionService,
        automation: AutomationService | None = None,
        faq: FAQService | None = None,
        audit: AuditService | None = None,
    ) -> None:
        self.pms = pms
        self.permissions = permissions
        self.automation = automation
        self.faq = faq or FAQService()
        self.audit = audit or AuditService()
        self._commands = self._build_commands()

    def _build_commands(self) -> dict[str, CommandDefinition]:
        return {
            "HELP": CommandDefinition("HELP", "Show available capabilities.", OperationType.READ, None),
            "GET_SYSTEM_STATUS": CommandDefinition("GET_SYSTEM_STATUS", "Show core service status.", OperationType.READ, None),
            "SEARCH_GUEST": CommandDefinition("SEARCH_GUEST", "Find a guest by name.", OperationType.READ, "pms.guest.read"),
            "GET_RESERVATION": CommandDefinition("GET_RESERVATION", "Find a reservation.", OperationType.READ, "pms.reservation.read"),
            "GET_ARRIVALS": CommandDefinition("GET_ARRIVALS", "Get arrivals for a date.", OperationType.READ, "pms.reservation.read"),
            "GET_DEPARTURES": CommandDefinition("GET_DEPARTURES", "Get departures for a date.", OperationType.READ, "pms.reservation.read"),
            "GET_ROOM_STATUS": CommandDefinition("GET_ROOM_STATUS", "Get a room or filtered room set.", OperationType.READ, "pms.room.read"),
            "MARK_ROOM_CLEAN": CommandDefinition("MARK_ROOM_CLEAN", "Mark a room clean.", OperationType.WRITE, "housekeeping.room.update"),
            "GET_INCIDENTS": CommandDefinition("GET_INCIDENTS", "Get incidents.", OperationType.READ, "pms.incident.read"),
            "CREATE_INCIDENT": CommandDefinition("CREATE_INCIDENT", "Create an incident.", OperationType.WRITE, "pms.incident.create", ConfirmationPolicy.REQUIRED),
            "RESOLVE_INCIDENT": CommandDefinition("RESOLVE_INCIDENT", "Resolve an incident.", OperationType.WRITE, "pms.incident.resolve", ConfirmationPolicy.RECOMMENDED),
            "GET_OPERATIONAL_SUMMARY": CommandDefinition("GET_OPERATIONAL_SUMMARY", "Get operational summary.", OperationType.READ, "management.reporting.read"),
            "FAQ_SEARCH": CommandDefinition("FAQ_SEARCH", "Search FAQ content.", OperationType.READ, None),
            "LIST_AUTOMATIONS": CommandDefinition("LIST_AUTOMATIONS", "List approved automations.", OperationType.READ, "automation.read"),
            "ENABLE_AUTOMATION": CommandDefinition("ENABLE_AUTOMATION", "Enable an approved automation.", OperationType.AUTOMATION, "automation.manage", ConfirmationPolicy.REQUIRED),
            "DISABLE_AUTOMATION": CommandDefinition("DISABLE_AUTOMATION", "Disable an approved automation.", OperationType.AUTOMATION, "automation.manage", ConfirmationPolicy.REQUIRED),
            "RUN_AUTOMATION": CommandDefinition("RUN_AUTOMATION", "Run an approved automation.", OperationType.AUTOMATION, "automation.execute", ConfirmationPolicy.REQUIRED),
            "GET_AUTOMATION_STATUS": CommandDefinition("GET_AUTOMATION_STATUS", "Get automation status.", OperationType.READ, "automation.read"),
            "GET_AUTOMATION_HISTORY": CommandDefinition("GET_AUTOMATION_HISTORY", "Get automation execution history.", OperationType.READ, "automation.read"),
        }

    def get(self, name: str) -> CommandDefinition | None:
        return self._commands.get(name.upper())

    def list_for(self, identity: Identity) -> list[CommandDefinition]:
        return [command for command in self._commands.values() if self.permissions.can(identity, command.permission)]

    def execute(self, identity: Identity, request: CommandRequest, *, confirmed: bool = False) -> CommandResult:
        command = self.get(request.name)
        if command is None:
            result = CommandResult(False, f"Unknown command: {request.name}", command=request.name)
            self.audit.record(identity, request.name, "UNKNOWN", False, parameters=request.parameters, details=result.message)
            return result
        if not self.permissions.can(identity, command.permission):
            result = CommandResult(False, "You are not authorized to perform this action.", command=command.name)
            self.audit.record(identity, command.name, command.operation_type.value, False, parameters=request.parameters, details="permission_denied")
            return result
        if command.confirmation == ConfirmationPolicy.REQUIRED and not confirmed:
            result = CommandResult(False, f"Confirmation required before executing {command.name}.", command=command.name)
            self.audit.record(identity, command.name, command.operation_type.value, False, parameters=request.parameters, details="confirmation_required")
            return result
        try:
            result_data = self._dispatch(command.name, request.parameters)
            result = CommandResult(True, self._format_message(command.name, result_data), result_data, command.name)
            self.audit.record(identity, command.name, command.operation_type.value, True, parameters=request.parameters)
            return result
        except (ValueError, KeyError) as exc:
            result = CommandResult(False, str(exc), command=command.name)
            self.audit.record(identity, command.name, command.operation_type.value, False, parameters=request.parameters, details=str(exc))
            return result
        except (TimeoutError, ConnectionError) as exc:
            result = CommandResult(False, "The PMS is temporarily unavailable. Please try again.", command=command.name)
            self.audit.record(identity, command.name, command.operation_type.value, False, parameters=request.parameters, details=str(exc))
            return result
        except Exception:
            result = CommandResult(False, "The requested operation could not be completed.", command=command.name)
            self.audit.record(identity, command.name, command.operation_type.value, False, parameters=request.parameters, details="internal_error")
            return result

    def _dispatch(self, name: str, params: dict[str, Any]) -> Any:
        if name == "HELP":
            return [c.name for c in self._commands.values()]
        if name == "GET_SYSTEM_STATUS":
            return {"pms": "available", "chatbot": "available", "ai": "not configured", "automation": "configured" if self.automation else "not configured"}
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
            return self.pms.create_incident(params.get("room_number"), self._required_text(params, "incident_type"), self._required_text(params, "description"))
        if name == "RESOLVE_INCIDENT":
            return self.pms.resolve_incident(self._required_text(params, "incident_id"))
        if name == "GET_OPERATIONAL_SUMMARY":
            return self.pms.get_operational_summary(self._parse_date(params.get("date")) if params.get("date") else None)
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

    @staticmethod
    def _format_message(command: str, result: Any) -> str:
        if command == "HELP":
            return "Available commands: " + ", ".join(result)
        if command == "GET_SYSTEM_STATUS":
            return "; ".join(f"{k}: {v}" for k, v in result.items())
        if command == "FAQ_SEARCH":
            matches = result.get("matches", [])
            if not matches:
                return "I couldn't find an answer in the approved FAQ content."
            return matches[0]["answer"]
        if isinstance(result, list):
            return f"Found {len(result)} result(s)."
        return str(result)
