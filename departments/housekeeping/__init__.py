from typing import List

from .housekeeping import HousekeepingChat

# Housekeeping does not invent new commands.
# It relies on the shared command registry and restricts its scope via permissions.
ALLOWED_COMMANDS: List[str] = [
    "GET_ROOM_STATUS",
    "MARK_ROOM_CLEAN",
    "GET_INCIDENTS",
    "RESOLVE_INCIDENT",
]


def get_housekeeping_permissions() -> List[str]:
    """Return the command names exposed to the housekeeping department."""
    return list(ALLOWED_COMMANDS)


__all__ = ["HousekeepingChat", "ALLOWED_COMMANDS", "get_housekeeping_permissions"]
