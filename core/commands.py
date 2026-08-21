from __future__ import annotations
from models.commands import CommandDefinition, OperationType, ConfirmationPolicy
from core.permissions import Identity, PermissionService

class CommandRegistry:
    def __init__(self, permissions: PermissionService) -> None:
        self.permissions = permissions
        self._commands = self._build_commands()

    def _build_commands(self) -> dict[str, CommandDefinition]:
        return { "HELP": CommandDefinition("HELP", "Show available capabilities.", OperationType.READ, None) } # ... truncated for brevity

    def get(self, name: str) -> CommandDefinition | None:
        return self._commands.get(name.upper())

    def list_for(self, identity: Identity) -> list[CommandDefinition]:
        return [command for command in self._commands.values() if self.permissions.can(identity, command.permission)]