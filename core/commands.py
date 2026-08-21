from __future__ import annotations

from models.command_params import (
    AutomationIdParams,
    CreateIncidentParams,
    DateParams,
    EmptyParams,
    FAQSearchParams,
    GetReservationParams,
    IncidentFilterParams,
    OperationalSummaryParams,
    ResolveIncidentParams,
    RoomNumberParams,
    RoomStatusParams,
    SearchGuestParams,
)
from models.commands import CommandDefinition, ConfirmationPolicy, OperationType
from core.permissions import Identity, PermissionService


class CommandRegistry:
    """Authoritative command definitions and capability lookup only."""

    def __init__(self, permissions: PermissionService) -> None:
        self.permissions = permissions
        self._commands = self._build_commands()

    def _build_commands(self) -> dict[str, CommandDefinition]:
        return {
            "HELP": CommandDefinition(
                "HELP", "Show available capabilities.", OperationType.READ, None, params_model=EmptyParams
            ),
            "GET_SYSTEM_STATUS": CommandDefinition(
                "GET_SYSTEM_STATUS", "Show core service status.", OperationType.READ, None, params_model=EmptyParams
            ),
            "SEARCH_GUEST": CommandDefinition(
                "SEARCH_GUEST", "Find a guest by name.", OperationType.READ, "pms.guest.read", params_model=SearchGuestParams
            ),
            "GET_RESERVATION": CommandDefinition(
                "GET_RESERVATION", "Find a reservation.", OperationType.READ, "pms.reservation.read", params_model=GetReservationParams
            ),
            "GET_ARRIVALS": CommandDefinition(
                "GET_ARRIVALS", "Get arrivals for a date.", OperationType.READ, "pms.reservation.read", params_model=DateParams
            ),
            "GET_DEPARTURES": CommandDefinition(
                "GET_DEPARTURES", "Get departures for a date.", OperationType.READ, "pms.reservation.read", params_model=DateParams
            ),
            "GET_ROOM_STATUS": CommandDefinition(
                "GET_ROOM_STATUS", "Get a room or filtered room set.", OperationType.READ, "pms.room.read", params_model=RoomStatusParams
            ),
            "MARK_ROOM_CLEAN": CommandDefinition(
                "MARK_ROOM_CLEAN", "Mark a room clean.", OperationType.WRITE, "housekeeping.room.update", params_model=RoomNumberParams
            ),
            "GET_INCIDENTS": CommandDefinition(
                "GET_INCIDENTS", "Get incidents.", OperationType.READ, "pms.incident.read", params_model=IncidentFilterParams
            ),
            "CREATE_INCIDENT": CommandDefinition(
                "CREATE_INCIDENT", "Create an incident.", OperationType.WRITE, "pms.incident.create",
                ConfirmationPolicy.REQUIRED, CreateIncidentParams
            ),
            "RESOLVE_INCIDENT": CommandDefinition(
                "RESOLVE_INCIDENT", "Resolve an incident.", OperationType.WRITE, "pms.incident.resolve",
                ConfirmationPolicy.RECOMMENDED, ResolveIncidentParams
            ),
            "GET_OPERATIONAL_SUMMARY": CommandDefinition(
                "GET_OPERATIONAL_SUMMARY", "Get operational summary.", OperationType.READ, "management.reporting.read",
                params_model=OperationalSummaryParams
            ),
            "FAQ_SEARCH": CommandDefinition(
                "FAQ_SEARCH", "Search FAQ content.", OperationType.READ, None, params_model=FAQSearchParams
            ),
            "LIST_AUTOMATIONS": CommandDefinition(
                "LIST_AUTOMATIONS", "List approved automations.", OperationType.READ, "automation.read", params_model=EmptyParams
            ),
            "ENABLE_AUTOMATION": CommandDefinition(
                "ENABLE_AUTOMATION", "Enable an approved automation.", OperationType.AUTOMATION, "automation.manage",
                ConfirmationPolicy.REQUIRED, AutomationIdParams
            ),
            "DISABLE_AUTOMATION": CommandDefinition(
                "DISABLE_AUTOMATION", "Disable an approved automation.", OperationType.AUTOMATION, "automation.manage",
                ConfirmationPolicy.REQUIRED, AutomationIdParams
            ),
            "RUN_AUTOMATION": CommandDefinition(
                "RUN_AUTOMATION", "Run an approved automation.", OperationType.AUTOMATION, "automation.execute",
                ConfirmationPolicy.REQUIRED, AutomationIdParams
            ),
            "GET_AUTOMATION_STATUS": CommandDefinition(
                "GET_AUTOMATION_STATUS", "Get automation status.", OperationType.READ, "automation.read",
                params_model=AutomationIdParams
            ),
            "GET_AUTOMATION_HISTORY": CommandDefinition(
                "GET_AUTOMATION_HISTORY", "Get automation execution history.", OperationType.READ, "automation.read",
                params_model=AutomationIdParams
            ),
        }

    def get(self, name: str) -> CommandDefinition | None:
        return self._commands.get(name.upper())

    def list_for(self, identity: Identity) -> list[CommandDefinition]:
        return [command for command in self._commands.values() if self.permissions.can(identity, command.permission)]

    def all(self) -> tuple[CommandDefinition, ...]:
        return tuple(self._commands.values())

    def names_for(self, identity: Identity) -> list[str]:
        return [command.name for command in self.list_for(identity)]
