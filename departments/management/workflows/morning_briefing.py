"""
Morning Briefing Workflow for Management.

This workflow defines the steps management takes to review the hotel's status,
utilizing the existing shared command registry rather than creating new commands.
"""

WORKFLOW_STEPS = [
    "1. Call GET_OPERATIONAL_SUMMARY to get a high-level view of arrivals, departures, and incidents.",
    "2. Call LIST_AUTOMATIONS to check the status of scheduled automated tasks (e.g., NIGHT_AUDIT).",
    "3. Call GET_AUTOMATION_HISTORY to review the outcome of the previous night's automated runs.",
    "4. Call RUN_AUTOMATION (requires confirmation) if any critical automation needs to be manually re-triggered."
]

def get_morning_briefing_workflow() -> list:
    """
    Returns the ordered steps for the morning briefing workflow.
    The actual execution of these steps relies on the shared CommandExecutor.
    """
    return WORKFLOW_STEPS