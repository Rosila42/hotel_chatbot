from typing import List

# Housekeeping does not invent new commands. 
# It relies on the shared command registry and restricts its scope via permissions.
ALLOWED_COMMANDS: List[str] = [
    "GET_ROOM_STATUS",      # read
    "MARK_ROOM_CLEAN",      # write, requires confirmation
    "GET_INCIDENTS",        # read
    "RESOLVE_INCIDENT",     # write, requires confirmation
]

def get_housekeeping_permissions() -> List[str]:
    """Returns the list of command names the housekeeping department is permitted to use."""
    return ALLOWED_COMMANDS