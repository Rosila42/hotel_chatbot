from typing import Dict, Any

# Shift-specific contextual hints for the Reception department.
# These do NOT change the available command sets, only the contextual hints 
# provided to the UI or the LLM parser.
SHIFT_CONTEXT: Dict[str, Dict[str, Any]] = {
    "morning": {
        "shift_name": "Morning",
        "focus": ["arrivals", "room readiness"],
        "suggested_prompts": [
            "today's arrivals",
            "which rooms are not ready?"
        ],
        "system_prompt_hint": "Focus on checking in arrivals and ensuring rooms are marked ready."
    },
    "afternoon": {
        "shift_name": "Afternoon",
        "focus": ["departures", "mid-day incidents"],
        "suggested_prompts": [
            "who is leaving today?",
            "show open incidents"
        ],
        "system_prompt_hint": "Focus on processing departures and resolving mid-day incidents."
    },
    "night": {
        "shift_name": "Night",
        "focus": ["audit", "security walk", "next-day prep"],
        "suggested_prompts": [
            "run automation NIGHT_AUDIT",
            "operational summary"
        ],
        "system_prompt_hint": "Focus on night audit, security walks, and preparing for the next day."
    }
}

def get_shift_context(shift: str) -> Dict[str, Any]:
    """
    Returns the contextual hints for a specific reception shift.
    Defaults to morning if an unknown shift is provided.
    """
    if not shift:
        return SHIFT_CONTEXT["morning"]
    
    # Normalize the input (e.g., "Morning", "MORNING" -> "morning")
    safe_shift = shift.lower().strip()
    return SHIFT_CONTEXT.get(safe_shift, SHIFT_CONTEXT["morning"])