# Hotel PMS Chatbot V2 — Command Registry Specification

## Status

Planning specification. No application implementation is authorized by this document.

## 1. Purpose

The command registry is the boundary between natural-language interaction and deterministic application execution.

The registry is the single execution contract for deterministic intent recognition and future optional AI/LLM interpretation.

Pipeline:

```text
User message
   ↓
Intent recognition
   ↓
Command Registry
   ↓
Validation
   ↓
Permission
   ↓
Confirmation if required
   ↓
Service
   ↓
PMS / FAQ / Automation
```

AI must not have a parallel trusted execution path.

## 2. Command Contract

Each command definition contains, conceptually:

- `name`
- `category`
- `description`
- `parameters`
- `validation`
- `permission`
- `operation_type` (`READ`, `WRITE`, `AUTOMATION`)
- `confirmation_policy`
- `handler/service`
- `response_schema`
- `data_minimization_policy`

## 3. Naming Principles

Commands describe capabilities, not departments. Shared PMS resources use shared commands. Department modules provide workflow/context instead of duplicating PMS primitives.

## 4. Final V1 Command Catalog

### System

- `HELP`
- `GET_SYSTEM_STATUS`

### PMS — Guest and Reservations

- `SEARCH_GUEST`
- `GET_RESERVATION`
- `GET_ARRIVALS`
- `GET_DEPARTURES`

### PMS — Rooms

- `GET_ROOM_STATUS`
- `MARK_ROOM_CLEAN`

`GET_ROOM_STATUS` supports one room or approved filters such as `available`, `dirty`, `cleaning`, `ready`, `maintenance`, `not_ready_arrivals`.

### PMS — Incidents

- `GET_INCIDENTS`
- `CREATE_INCIDENT`
- `RESOLVE_INCIDENT`

`CREATE_INCIDENT` is generic; department/type restrictions are enforced by permission and validation. Do not create a separate `REPORT_HOUSEKEEPING_ISSUE` command.

### PMS — Operations

- `GET_OPERATIONAL_SUMMARY`

The summary may include arrivals, departures, occupancy, available rooms, rooms requiring attention, and open incidents. Do not create separate summary-field commands in V1 without a concrete requirement.

### FAQ

- `FAQ_SEARCH`

Ordinary FAQ retrieval is deterministic; an LLM is not required.

### Automation

- `LIST_AUTOMATIONS`
- `ENABLE_AUTOMATION`
- `DISABLE_AUTOMATION`
- `RUN_AUTOMATION`
- `GET_AUTOMATION_STATUS`
- `GET_AUTOMATION_HISTORY`

V1 automation uses predefined templates. Arbitrary natural-language workflow authoring is out of scope.

`CONFIRM` and `CANCEL` are session/action-state controls, not ordinary PMS commands.

## 5. Command Details

### `HELP`

Operation: `READ`

Permission: authenticated user.

Parameters: none.

Expected result: context/role-aware list of supported capabilities.

### `GET_SYSTEM_STATUS`

Operation: `READ`

Permission: authenticated user.

Parameters: none.

Expected result may distinguish chatbot/API, PMS connectivity, automation worker, and AI availability. Do not expose credentials or stack traces.

### `SEARCH_GUEST`

Operation: `READ`

Permission: `pms.guest.read`.

Parameters: `name`, optionally other explicitly supported lookup identifiers.

Validation: at least one meaningful search criterion; normalize supported formats; avoid uncontrolled broad queries.

Response policy: only fields required for the task. Do not automatically expose government ID, passport data, payment information, credentials, or unnecessary sensitive notes.

### `GET_RESERVATION`

Operation: `READ`

Permission: `pms.reservation.read`.

Parameters may include `reservation_id`, `guest_name`, and bounded date/range filters.

Validation: meaningful lookup criterion, bounded result set, explicit ambiguity handling.

### `GET_ARRIVALS`

Operation: `READ`

Permission: `pms.reservation.read`.

Parameters: `date` defaulting to the hotel business date/today; optional bounded date/range and approved filters.

### `GET_DEPARTURES`

Operation: `READ`

Permission: `pms.reservation.read`.

Parameters: `date` defaulting to the hotel business date/today; optional bounded date/range and approved filters.

### `GET_ROOM_STATUS`

Operation: `READ`

Permission: `pms.room.read`.

Parameters: optional `room_number`, `filter`, `date`.

The PMSService owns composition such as `not_ready_arrivals`. The chatbot core must not loop over PMS entities to construct business results.

### `MARK_ROOM_CLEAN`

Operation: `WRITE`

Permission: `housekeeping.room.update` or equivalent.

Parameter: `room_number`.

Validation: room exists, current state permits transition, caller authorized, PMS accepts transition.

Confirmation: normally none for V1.

Audit: required.

### `GET_INCIDENTS`

Operation: `READ`

Permission: `pms.incident.read`.

Optional filters: `status`, `department`, `room_number`, `priority`, bounded date range.

### `CREATE_INCIDENT`

Operation: `WRITE`

Permission: `pms.incident.create`, with type/department restrictions where needed.

Required parameters: `description`, `incident_type`.

Optional parameters: `priority`, `room_number`, relevant guest/reservation reference.

Validation: required fields, canonical incident type, target existence, permission, PMS payload rules.

Confirmation: `REQUIRED` by default for conversational creation.

Audit: required.

Example: `The AC in 214 is broken` → draft incident → user confirms → execute.

### `RESOLVE_INCIDENT`

Operation: `WRITE`

Permission: `pms.incident.resolve` or equivalent.

Parameters: `incident_id`, optional resolution note.

Validation: incident exists, is resolvable, caller authorized, PMS accepts transition.

Confirmation: recommended/required depending on PMS semantics.

Audit: required.

Do not implement generic `UPDATE_INCIDENT` in V1.

### `GET_OPERATIONAL_SUMMARY`

Operation: `READ`

Permission: `management.reporting.read` for full management scope; narrower visibility may be added by role policy.

Optional parameters: scope, shift, as-of date/time.

Result may include arrivals, departures, occupancy, availability, room attention, open incidents, and approved operational metrics.

### `FAQ_SEARCH`

Operation: `READ`

Permission: authenticated user subject to knowledge-scope policy.

Parameter: `query`.

Validation: non-empty, bounded length.

Response: authoritative approved hotel/FAQ content.

Optional future AI may synthesize retrieved approved content, but the source remains authoritative.

### `LIST_AUTOMATIONS`

Operation: `AUTOMATION`/`READ`.

Permission: `automation.read`.

Parameters: optional approved status/department filters.

### `ENABLE_AUTOMATION`

Operation: `AUTOMATION`.

Permission: `automation.manage`.

Parameters: automation/template id plus only approved configuration parameters.

Validation: template exists, configuration valid, schedule valid, caller authorized.

Confirmation: `REQUIRED`.

Audit: required.

### `DISABLE_AUTOMATION`

Operation: `AUTOMATION`.

Permission: `automation.manage`.

Parameter: automation id.

Validation: automation exists and caller authorized.

Confirmation: normally required.

Audit: required.

### `RUN_AUTOMATION`

Operation: `AUTOMATION` and potentially `WRITE` depending on workflow.

Permission: `automation.execute`.

Parameter: automation id plus any explicitly supported runtime parameters.

Validation: approved template, authorization, execution lock/concurrency policy.

Confirmation: `REQUIRED` when side effects exist.

Audit: required.

### `GET_AUTOMATION_STATUS`

Operation: `READ`.

Permission: `automation.read`.

Parameter: automation id.

Possible statuses: `ENABLED`, `DISABLED`, `RUNNING`, `COMPLETED`, `FAILED`, `PARTIAL`.

### `GET_AUTOMATION_HISTORY`

Operation: `READ`.

Permission: `automation.read`.

Parameters: automation id and bounded history range/limit.

Execution history must preserve partial execution. Example: 10 expected, 3 completed, PMS timeout, 7 not attempted.

## 6. Session Actions

### `CONFIRM`

Confirms a pending action stored in the session state. It must not accept arbitrary business parameters.

Validation: pending action exists, is not expired, user/session remains authorized, confirmation context matches.

Execution: stored action is re-submitted through the normal command registry with confirmation granted.

### `CANCEL`

Cancels the pending action and clears pending session state.

## 7. Confirmation Policy

Each write/automation command declares `NONE`, `RECOMMENDED`, or `REQUIRED`.

Initial V1:

| Command | Policy |
|---|---|
| `MARK_ROOM_CLEAN` | `NONE` |
| `CREATE_INCIDENT` | `REQUIRED` |
| `RESOLVE_INCIDENT` | `RECOMMENDED`/`REQUIRED` depending on PMS semantics |
| `ENABLE_AUTOMATION` | `REQUIRED` |
| `DISABLE_AUTOMATION` | `REQUIRED` |
| `RUN_AUTOMATION` | `REQUIRED` when side effects exist |

Scheduled execution of an already-enabled automation does not require interactive confirmation on every run.

## 8. Permission Model

Conceptual permissions:

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

The exact identifiers may be refined with the host-PMS identity model.

Department/type restrictions must not widen permissions accidentally.

## 9. Data Minimization / Response Schemas

Permission answers whether a user may call a resource. Response policy answers which fields may leave the service boundary.

Sensitive PMS fields must be excluded unless explicitly required and authorized.

For cloud AI, minimization occurs before data reaches the AI layer.

## 10. Error Behavior

Commands distinguish invalid parameters, ambiguity, permission denial, validation failure, PMS unavailability, PMS rejection, and internal error.

Never claim a write succeeded unless the PMS/automation subsystem confirmed it.

Return clear operational errors rather than stack traces.

## 11. Ambiguous Intent

Low-confidence or tied deterministic intent must not guess.

Example:

```text
I can help with room 214. Did you mean:
1. Check room status
2. Mark room clean
3. Report an incident
```

If AI is used for interpretation, its output uses the same registry, validation, permission, and confirmation path.

## 12. AI Structured Command Contract

Future AI output identifies exactly one registry command at a time:

```json
{
  "command": "GET_ROOM_STATUS",
  "parameters": {
    "room_number": "214"
  }
}
```

Unknown or invalid commands are rejected. An LLM must never gain authority to execute arbitrary SQL, code, or unsupported PMS operations.

V1 does not permit autonomous arbitrary lists of PMS mutations from the LLM.

## 13. Composite Query Rule

Cross-resource business composition belongs in `PMSService`, not the chatbot core.

```text
Command
 ↓
PMSService
 ↓
PMS Adapter(s)
 ↓
PMS
```

The adapter translates vendor-specific semantics; PMSService composes and normalizes application-level results.

## 14. Automation Template Rule

V1 automations are predefined templates, for example `MORNING_ARRIVAL_CHECK`.

Controlled parameters may include schedule/time and notification target.

Do not implement arbitrary condition/action trees in V1.

Future AI may map natural language to `template_id + validated parameters` but may not author arbitrary workflow logic.

## 15. Out-of-Scope Commands

- bulk room updates
- generic room-detail editing
- room out-of-service operations
- generic room-status mutation
- reservation note editing
- housekeeping task-management subsystem
- operational trend analytics
- arbitrary automation authoring
- full reservation creation/cancellation workflows
- payment/billing commands
- multi-property management
- direct PMS database commands

## 16. Registry Acceptance Criteria

1. Every V1 command has an owner service.
2. Every command has explicit parameters and validation.
3. Every command has a permission.
4. Every write/automation operation has a confirmation policy.
5. Every PMS read has a response/data-minimization policy.
6. Every mutation is auditable.
7. AI and deterministic intent use the same registry and validation path.
8. No command requires direct database access.
9. No department-specific duplicate exists for a shared PMS capability.
10. The catalog does not recreate a full PMS UI through chat.

## 17. Implementation Gate

This document is a planning artifact only. Implementation begins only after explicit human approval.
