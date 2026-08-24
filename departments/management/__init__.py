from typing import List

# Management does not invent new commands. 
# It restricts its scope via permissions to high-level operational and automation commands.
ALLOWED_COMMANDS: List[str] = [
    "GET_OPERATIONAL_SUMMARY",  # read
    "LIST_AUTOMATIONS",         # read
    "RUN_AUTOMATION",           # write, requires confirmation
    "GET_AUTOMATION_HISTORY"    # read
]

def get_management_permissions() -> List[str]:
    """Returns the list of command names the management department is permitted to use."""
    return ALLOWED_COMMANDS