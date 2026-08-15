# Hotel PMS Chatbot V2 — Command Registry Specification

## Status

Planning specification. No application implementation is authorized by this document.

The registry is the boundary between natural-language interaction and deterministic application execution. AI and deterministic intent must use the same command registry, validation, permission, confirmation, service, and execution path.

## Final V1 command catalog

### System
- HELP
- GET_SYSTEM_STATUS

### PMS — Guests/Reservations
- SEARCH_GUEST
- GET_RESERVATION
- GET_ARRIVALS
- GET_DEPARTURES

### PMS — Rooms
- GET_ROOM_STATUS
- MARK_ROOM_CLEAN

### PMS — Incidents
- GET_INCIDENTS
- CREATE_INCIDENT
- RESOLVE_INCIDENT

### PMS — Operations
- GET_OPERATIONAL_SUMMARY

### FAQ
- FAQ_SEARCH

### Automation
- LIST_AUTOMATIONS
- ENABLE_AUTOMATION
- DISABLE_AUTOMATION
- RUN_AUTOMATION
- GET_AUTOMATION_STATUS
- GET_AUTOMATION_HISTORY

`CONFIRM` and `CANCEL` are session/action-state controls.

## Core rules

- Commands describe shared capabilities, not departments.
- PMS composition belongs in PMSService, not the chatbot core.
- PMS reads have explicit response/data-minimization policies.
- PMS mutations are permissioned and audited.
- V1 automation uses predefined templates.
- Direct PMS DB access is out of scope for V1.
- V1 does not permit arbitrary autonomous multi-step PMS mutations from the LLM.
