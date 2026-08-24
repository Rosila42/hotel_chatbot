from typing import List

from .manager import ManagementChat

# Management does not invent new commands.
# It restricts its scope via permissions to high-level operational and automation commands.
ALLOWED_COMMANDS: List[str] = [
    "GET_OPERATIONAL_SUMMARY",
    "LIST_AUTOMATIONS",
    "RUN_AUTOMATION",
    "GET_AUTOMATION_HISTORY",
]


def get_management_permissions() -> List[str]:
    """Return the command names exposed to the management department."""
    return list(ALLOWED_COMMANDS)


__all__ = ["ManagementChat", "ALLOWED_COMMANDS", "get_management_permissions"]
