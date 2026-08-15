# Hotel PMS Chatbot V2 — Command Registry Specification

## Status

Planning specification. No application implementation is authorized by this document.

## 1. Purpose

The command registry is the boundary between natural-language interaction and deterministic application execution.

The registry must be the single execution contract for both:

- deterministic intent recognition;
- future optional AI/LLM interpretation.

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

Each command definition must contain, conceptually:

- `name`
- `category`
- `description`
- `parameters`
- `validation`
- `permission`
- `operation_type` (`READ`, `WRITE`, or `AUTOMATION`)
- `confirmation_policy`
- `handler/service`
- `response_schema`
- `data_minimization_policy`

The implementation may use a registry object, decorators, metadata classes, or another mechanism, provided there is one authoritative registry.

## 3. Naming Principles

Commands describe **capabilities**, not departments.

Shared PMS resources use shared commands.

Do not create parallel commands such as:

- `GET_RECEPTION_ROOM_STATUS`
- `GET_HOUSEKEEPING_ROOM_STATUS`

Use one `GET_ROOM_STATUS` command and control access through permissions/context.

Department modules provide workflow/context, not duplicate PMS primitives.

## 4. Final V1 Command Catalog

### 4.1 System

#### `HELP`

Purpose: Show capabilities available to the current user/context.

Operation: `READ`

Permission: authenticated user.

Parameters: none.

Validation: none.

Confirmation: none.

Expected result: role/context-aware help content.

#### `GET_SYSTEM_STATUS`

Purpose: Report application/PMS/automation/AI availability as applicable.

Operation: `READ`

Permission: authenticated user.

Parameters: none.

Validation: none.

Confirmation: none.

Expected result should distinguish, where supported:

- chatbot/API availability;
- PMS connectivity;
- automation worker availability;
- AI availability.

Do not expose internal credentials, stack traces, or sensitive infrastructure details.

---

### 4.2 PMS — Guest and Reservations

#### `SEARCH_GUEST`

Purpose: Find a guest using authorized identifying information.

Operation: `READ`

Suggested parameters:

- `name`
- `reservation_id` (optional)
- other explicitly supported search criteria only

Validation:

- at least one meaningful search criterion;
- normalize/validate supported formats;
- reject ambiguous/high-risk searches where policy requires narrowing.

Permission: appropriate guest-read capability, e.g. `pms.guest.read`.

Confirmation: none.

Response policy:

Return only fields authorized and necessary for the requested task.

Do not automatically expose:

- government ID;
- passport data;
- payment information;
- credentials;
- unnecessary sensitive notes.

#### `GET_RESERVATION`

Purpose: Retrieve or locate a reservation.

Operation: `READ`

Suggested parameters:

- `reservation_id` (optional)
- `guest_name` (optional)
- `date`/date range (optional)
- other supported PMS search criteria

Validation:

- at least one meaningful lookup criterion;
- enforce result limits;
- handle ambiguous matches explicitly.

Permission: `pms.reservation.read`.

Confirmation: none.

Response policy: return only the minimum required reservation fields.

#### `GET_ARRIVALS`

Purpose: Retrieve arrivals for a date or supported date range.

Operation: `READ`

Parameters:

- `date` (default: current hotel business date/today)
- optional supported range
- optional filters where supported

Validation:

- valid date/date range;
- bounded range to avoid uncontrolled queries.

Permission: `pms.reservation.read`.

Confirmation: none.

Expected result: structured arrivals, not raw PMS JSON.

Potential filters such as "pending" may be implemented through the PMSService without introducing another command.

#### `GET_DEPARTURES`

Purpose: Retrieve departures for a date or supported date range.

Operation: `READ`

Parameters:

- `date` (default: current hotel business date/today)
- optional supported range
- optional filters where supported

Validation: valid/bounded date range.

Permission: `pms.reservation.read`.

Confirmation: none.

---

### 4.3 PMS — Rooms

#### `GET_ROOM_STATUS`

Purpose: Retrieve room status for one room or a filtered room set.

Operation: `READ`

Parameters may include:

- `room_number` (optional)
- `filter` (optional)
- `date` (optional where relevant)

Supported conceptual filters may include:

- `available`
- `dirty`
- `cleaning`
- `ready`
- `maintenance`
- `not_ready_arrivals`

The exact filter vocabulary must be canonical and documented.

Validation:

- room identifier must be valid if supplied;
- filter must be in the approved vocabulary;
- date ranges must be bounded.

Permission: shared `pms.room.read`.

Confirmation: none.

Important: the PMSService may compose multiple underlying PMS calls to answer filters such as `not_ready_arrivals`. The chatbot core must not perform the composition.

Response policy: return only room fields required by the requester/context.

#### `MARK_ROOM_CLEAN`

Purpose: Mark a room as cleaned/ready according to the PMS workflow.

Operation: `WRITE`

Parameter:

- `room_number` (required)

Validation:

- room exists;
- current state allows the transition;
- caller is authorized;
- PMS accepts the transition.

Permission: `housekeeping.room.update` (or equivalent approved permission).

Confirmation: normally none for the V1 demo if the operation is considered low risk.

Audit: required.

Important: this command should invoke a controlled PMS operation rather than directly changing a local database field.

---

### 4.4 PMS — Incidents

#### `GET_INCIDENTS`

Purpose: Retrieve relevant incidents.

Operation: `READ`

Parameters may include:

- `status` (optional)
- `department` (optional, if authorized)
- `room_number` (optional)
- `priority` (optional)
- bounded date range (optional)

Validation: only approved filter values; bounded queries.

Permission: `pms.incident.read`.

Confirmation: none.

Response should contain structured incident information.

#### `CREATE_INCIDENT`

Purpose: Create an incident in the PMS.

Operation: `WRITE`

Parameters:

- `description` (required)
- `incident_type` (required)
- `priority` (optional/defaulted according to policy)
- `room_number` and/or relevant guest/reservation reference where supported

Validation:

- required fields present;
- `incident_type` from canonical vocabulary;
- target resource exists;
- caller has permission to create that incident type;
- payload within PMS limits.

Permission: base capability such as `pms.incident.create`, with department/type restrictions where necessary.

Confirmation: required by default for conversational creation in V1 because natural-language input may be ambiguous.

Example:

```text
User: "The AC in 214 is broken."
Bot: "I can create a maintenance incident for room 214: AC not working. Confirm?"
User: "Confirm."
```

Audit: required.

#### `RESOLVE_INCIDENT`

Purpose: Resolve/close an existing incident using the PMS-supported resolution operation.

Operation: `WRITE`

Parameters:

- `incident_id` (required)
- optional `resolution_note` where supported

Validation:

- incident exists;
- incident is currently resolvable;
- caller has resolution permission;
- PMS accepts the transition.

Permission: `pms.incident.resolve` (or equivalent approved permission).

Confirmation: may be required depending on policy; default to explicit confirmation if resolution has meaningful operational consequences.

Audit: required.

Do not implement generic `UPDATE_INCIDENT` unless a real PMS integration later proves that a broader update capability is required.

---

### 4.5 PMS — Operations

#### `GET_OPERATIONAL_SUMMARY`

Purpose: Produce a structured operational overview for the current user/role.

Operation: `READ`

Parameters may include:

- `scope` (optional)
- `shift` (optional)
- `as_of` (optional)

The result may include:

- arrivals;
- departures;
- occupancy;
- available rooms;
- rooms requiring attention;
- open incidents;
- other approved operational metrics.

Permission: `management.reporting.read` for full management scope; narrower role-based visibility may be defined for other departments.

Confirmation: none.

Important: do not create separate top-level V1 commands merely for each summary field such as `GET_OCCUPANCY` or `GET_ROOM_STATUS_SUMMARY` unless an actual product requirement later justifies them.

---

### 4.6 FAQ

#### `FAQ_SEARCH`

Purpose: Retrieve an authoritative answer from approved FAQ/hotel-policy content.

Operation: `READ`

Parameters:

- `query` (required)
- optional category

Validation:

- query non-empty;
- safe length limit.

Permission: authenticated users, subject to content scope.

Confirmation: none.

Response policy:

Return authoritative approved content.

Do not use an LLM for ordinary FAQ lookup in V1.

Optional future AI may synthesize or explain retrieved approved content while preserving the underlying source.

---

### 4.7 Automation

Automation commands operate on predefined templates/workflows.

V1 must not provide arbitrary natural-language workflow authoring.

#### `LIST_AUTOMATIONS`

Purpose: List automation templates/definitions available to the current user.

Operation: `AUTOMATION`

Permission: `automation.read`.

Parameters: optional department/status filter.

Expected result: automation name, purpose, enabled status, schedule/status information permitted for the user.

#### `ENABLE_AUTOMATION`

Purpose: Enable an approved automation template/definition.

Operation: `AUTOMATION`

Parameters:

- `automation_id` or template identifier
- approved configuration parameters only, such as schedule/notification target where supported

Validation:

- template exists;
- configuration matches allowed schema;
- caller has permission;
- schedule valid;
- notification target authorized.

Permission: `management.automation.manage` or equivalent approved permission.

Confirmation: required before enabling a new automation.

Audit: required.

#### `DISABLE_AUTOMATION`

Purpose: Disable an existing automation.

Operation: `AUTOMATION`

Parameters:

- `automation_id`

Validation: automation exists and caller is authorized.

Permission: `management.automation.manage`.

Confirmation: normally required.

Audit: required.

#### `RUN_AUTOMATION`

Purpose: Manually execute an approved/predefined automation.

Operation: `AUTOMATION` and potentially `WRITE` depending on workflow.

Parameters:

- `automation_id`
- optional explicitly supported runtime parameters

Validation:

- automation exists;
- enabled/allowed according to policy;
- caller authorized;
- execution is not already locked/running when concurrent execution is prohibited.

Permission: `management.automation.execute` or equivalent.

Confirmation: required for manual execution when the workflow can create PMS mutations or external notifications.

Audit: required.

#### `GET_AUTOMATION_STATUS`

Purpose: Retrieve status of a configured automation.

Operation: `READ`

Parameters:

- `automation_id`

Permission: `automation.read`.

Expected status values may include:

- `ENABLED`
- `DISABLED`
- `RUNNING`
- `COMPLETED`
- `FAILED`
- `PARTIAL`

#### `GET_AUTOMATION_HISTORY`

Purpose: Retrieve execution history for an automation.

Operation: `READ`

Parameters:

- `automation_id`
- bounded time range/limit

Permission: `automation.read`.

Execution history should capture partial execution.

Example:

```text
10 tasks expected
3 completed
PMS timeout
7 not attempted
```

Do not collapse this to a generic `FAILED` result.

## 5. Session Actions

`CONFIRM` and `CANCEL` are session/action-state controls, not PMS commands.

### `CONFIRM`

Purpose: confirm a pending write/automation action.

Input: no arbitrary business parameters. Operates only on the session's pending action.

Validation:

- pending action exists;
- pending action has not expired;
- session/user still authorized;
- confirmation context matches expected action.

Execution: re-run the stored validated action through the normal command path.

### `CANCEL`

Purpose: cancel a pending action without executing it.

Validation: pending action exists.

Result: clear pending action and return deterministic confirmation.

## 6. Confirmation Policy

Each write/automation command must declare a confirmation policy:

- `NONE`
- `RECOMMENDED`
- `REQUIRED`

Initial V1 recommendation:

| Command | Policy |
|---|---|
| `MARK_ROOM_CLEAN` | `NONE` |
| `CREATE_INCIDENT` | `REQUIRED` |
| `RESOLVE_INCIDENT` | `RECOMMENDED`/`REQUIRED` depending on PMS semantics |
| `ENABLE_AUTOMATION` | `REQUIRED` |
| `DISABLE_AUTOMATION` | `REQUIRED` |
| `RUN_AUTOMATION` | `REQUIRED` when workflow has side effects |

Scheduled execution of an already-enabled automation is governed by the automation's stored authorization policy and does not require interactive confirmation on every run.

## 7. Permission Model

Permissions should be capability-based and reusable across departments.

Initial conceptual permissions:

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

The exact final permission identifiers may be refined after the authentication/host-PMS model is defined.

Important: department/type-specific restrictions must not accidentally widen permissions. For example, housekeeping may be allowed to create housekeeping incidents but not arbitrary high-impact management incidents.

## 8. Data Minimization / Response Schemas

Every command that returns PMS data must have an explicit response policy.

A command's permission answers whether the user may call it.

The response policy answers which fields may leave the service boundary.

Sensitive PMS fields must be excluded unless explicitly required and authorized.

For cloud AI, minimization must happen before data reaches the AI layer.

## 9. Error Behavior

Commands must distinguish:

- invalid parameters;
- ambiguity;
- permission denied;
- validation failure;
- PMS unavailable;
- PMS rejection;
- internal error.

The chatbot must never claim a write succeeded unless the PMS or automation subsystem confirmed it.

For PMS timeouts/failures, return a clear operational message rather than a stack trace.

## 10. Ambiguous Intent Handling

Deterministic intent recognition should use the registry as its source of valid commands.

Low-confidence or tied recognition must not guess.

Example:

```text
I can help with room 214. Did you mean:
1. Check room status
2. Mark room clean
3. Report an incident
```

If AI is enabled, AI may be used as an additional interpretation step, but its output must pass through the exact same registry, validation, permission, and confirmation logic.

## 11. AI Structured Command Contract

Future AI intent output must identify exactly one registry command at a time.

Conceptual form:

```json
{
  "command": "GET_ROOM_STATUS",
  "parameters": {
    "room_number": "214"
  }
}
```

Invalid/unknown commands must be rejected.

Examples such as `DELETE_GUEST` or arbitrary SQL operations must never be accepted merely because an LLM returned them.

V1 does not permit an LLM to autonomously execute an arbitrary list of PMS mutations.

## 12. Composite Query Rule

A command such as:

`GET_ROOM_STATUS(filter=NOT_READY_ARRIVALS)`

may require multiple PMS operations.

The chatbot core must not perform the composition.

The responsibility is:

```text
Command
 ↓
PMSService
 ↓
PMS Adapter(s)
 ↓
PMS
```

PMSService may compose and normalize the result.

The Adapter remains responsible for vendor-specific translation.

## 13. Automation Template Rule

V1 automations are predefined templates.

Example template:

`MORNING_ARRIVAL_CHECK`

Potential controlled parameters:

- schedule/time;
- notification target;
- other template-defined fields.

Do not implement arbitrary user-defined condition/action trees in V1.

The LLM may eventually map natural language to:

`template_id + validated parameters`

but may not author arbitrary workflow logic.

## 14. Out-of-Scope Commands

The following are explicitly out of V1:

- bulk room updates
- generic room detail editing
- room out-of-service operations
- generic room status mutation
- reservation note editing
- housekeeping task-management subsystem
- operational trend analytics
- arbitrary automation authoring
- full reservation creation/cancellation workflows
- payment/billing commands
- multi-property management
- direct PMS database commands

## 15. Registry Acceptance Criteria

The registry specification is complete when:

1. every V1 command has an owner service;
2. every command has explicit parameters and validation;
3. every command has a permission;
4. every write/automation operation has a confirmation policy;
5. every PMS read has a response/data-minimization policy;
6. every mutation is auditable;
7. AI and deterministic intent use the same registry and validation path;
8. no command requires direct database access;
9. no department-specific duplicate exists for a shared PMS capability;
10. the catalog does not recreate a full PMS UI through chat.

## 16. Implementation Gate

This document is a planning artifact only.

No implementation should begin until the human explicitly approves the implementation plan and command specification.
