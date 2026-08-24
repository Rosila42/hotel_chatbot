"""
Room Readiness Workflow for Housekeeping.

This workflow defines the steps housekeeping takes to process rooms,
utilizing the existing shared command registry rather than creating new commands.
"""

WORKFLOW_STEPS = [
    "1. Call GET_ROOM_STATUS (filter: dirty) to identify rooms needing attention.",
    "2. Call MARK_ROOM_CLEAN (requires confirmation) once a room is physically cleaned.",
    "3. Call GET_INCIDENTS (filter: room_id) to check for any reported maintenance issues.",
    "4. Call RESOLVE_INCIDENT (requires confirmation) if an incident is marked as handled."
]

def get_room_readiness_workflow() -> list:
    """
    Returns the ordered steps for the room readiness workflow.
    The actual execution of these steps relies on the shared CommandExecutor.
    """
    return WORKFLOW_STEPS