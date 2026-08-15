# Hotel PMS Chatbot V2 — Command Registry Specification

## Status

Planning specification. No application implementation is authorized by this document.

The full approved command specification is retained from the planning baseline commit and remains the authoritative command contract for V2.

## Final V1 command set

- HELP
- GET_SYSTEM_STATUS
- SEARCH_GUEST
- GET_RESERVATION
- GET_ARRIVALS
- GET_DEPARTURES
- GET_ROOM_STATUS
- MARK_ROOM_CLEAN
- GET_INCIDENTS
- CREATE_INCIDENT
- RESOLVE_INCIDENT
- GET_OPERATIONAL_SUMMARY
- FAQ_SEARCH
- LIST_AUTOMATIONS
- ENABLE_AUTOMATION
- DISABLE_AUTOMATION
- RUN_AUTOMATION
- GET_AUTOMATION_STATUS
- GET_AUTOMATION_HISTORY

`CONFIRM` and `CANCEL` are session/action-state controls, not ordinary PMS commands.

AI and deterministic intent must use the same registry, validation, permission, confirmation, service, and execution path.

Shared PMS capabilities are not duplicated by department.
