# Hotel PMS Chatbot V2 — Command Registry Specification

## Status

Planning specification. No application implementation is authorized by this document.

## Purpose

The command registry is the single execution contract between natural-language interaction and deterministic application behavior. Both deterministic and AI-derived intent must use the same registry, validation, permission, confirmation, and service path.

## Final V1 command catalog

### System
- `HELP`
- `GET_SYSTEM_STATUS`

### PMS — Guest/Reservations
- `SEARCH_GUEST`
- `GET_RESERVATION`
- `GET_ARRIVALS`
- `GET_DEPARTURES`

### PMS — Rooms
- `GET_ROOM_STATUS`
- `MARK_ROOM_CLEAN`

`GET_ROOM_STATUS` is shared across departments and supports approved room/filter queries. Cross-resource composition such as `not_ready_arrivals` belongs in `PMSService`.

### PMS — Incidents
- `GET_INCIDENTS`
- `CREATE_INCIDENT`
- `RESOLVE_INCIDENT`

`CREATE_INCIDENT` is the shared incident creation capability; do not create separate department-specific incident commands.

### PMS — Operations
- `GET_OPERATIONAL_SUMMARY`

### FAQ
- `FAQ_SEARCH`

### Automation
- `LIST_AUTOMATIONS`
- `ENABLE_AUTOMATION`
- `DISABLE_AUTOMATION`
- `RUN_AUTOMATION`
- `GET_AUTOMATION_STATUS`
- `GET_AUTOMATION_HISTORY`

V1 automation uses predefined templates rather than arbitrary workflow authoring.

`CONFIRM` and `CANCEL` are session/action-state controls, not ordinary PMS commands.

## Command contract

Each command defines conceptually:

- name
- category
- parameters
- validation
- permission
- operation type
- confirmation policy
- owning service
- response/data-minimization policy

## Security and AI rules

- PMS remains authoritative.
- PMS mutations are permissioned and audited.
- Sensitive fields are excluded unless explicitly required and authorized.
- AI output is untrusted input.
- AI must return one structured registry command at a time in V1.
- AI cannot directly access PMS, SQL, or code execution.
- No alternate trusted AI execution path exists.

## Confirmation

Initial V1 policy:

| Command | Policy |
|---|---|
| `MARK_ROOM_CLEAN` | NONE |
| `CREATE_INCIDENT` | REQUIRED |
| `RESOLVE_INCIDENT` | RECOMMENDED/REQUIRED depending on PMS semantics |
| `ENABLE_AUTOMATION` | REQUIRED |
| `DISABLE_AUTOMATION` | REQUIRED |
| `RUN_AUTOMATION` | REQUIRED when side effects exist |

Scheduled execution of an already-enabled automation does not require interactive confirmation every run.

## Permissions

Conceptual capabilities:

```text
pms.guest.read
pms.reservation.read
pms.room.read
housekeeping.room.update
pms.incident.read
pms.incident.create
pms.incident.resolve
management.reporting.read
automation.read
automation.manage
automation.execute
```

## Error/ambiguity behavior

Commands must distinguish validation errors, ambiguity, permission denial, PMS rejection/unavailability, and internal failures. Low-confidence intent must not guess. A clarification menu is preferred.

## V1 exclusions

- bulk room updates
- generic room-detail editing
- room out-of-service operations
- generic room-status mutation
- reservation note editing
- housekeeping task subsystem
- operational trend analytics
- arbitrary automation authoring
- full reservation creation/cancellation workflows
- payment/billing commands
- multi-property management
- direct PMS database commands

## Implementation gate

This document is a planning artifact only. Implementation was authorized separately by the human and should continue in small, reviewable commits. 
