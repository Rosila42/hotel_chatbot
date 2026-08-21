from __future__ import annotations
from datetime import date
from typing import Any
from models.commands import CommandDefinition, CommandRequest, CommandResult
from core.permissions import Identity
from services.audit_service import AuditService
from services.automation_service import AutomationService
from services.faq_service import FAQService
from services.pms_service import PMSService
from services.response_formatter import ResponseFormatter

class CommandExecutor:
    def __init__(self, pms: PMSService, automation: AutomationService | None = None, faq: FAQService | None = None, audit: AuditService | None = None) -> None:
        self.pms = pms
        self.automation = automation
        self.faq = faq or FAQService()
        self.audit = audit or AuditService()
        self.formatter = ResponseFormatter()

    def execute(self, identity: Identity, request: CommandRequest, command: CommandDefinition) -> CommandResult:
        try:
            result_data = self._dispatch(command.name, request.parameters)
            message = self.formatter.format(command.name, result_data)
            result = CommandResult(True, message, result_data, command.name)
            self.audit.record(identity, command.name, command.operation_type.value, True, parameters=request.parameters)
            return result
        except (ValueError, KeyError) as exc:
            result = CommandResult(False, str(exc), command=command.name)
            self.audit.record(identity, command.name, command.operation_type.value, False, parameters=request.parameters, details=str(exc))
            return result
        # ... (TimeoutError/ConnectionError and generic Exception handling omitted for brevity)

    def _dispatch(self, name: str, params: dict[str, Any]) -> Any:
        # Massive if/elif tree mapping commands to self.pms, self.faq, self.automation methods
        pass