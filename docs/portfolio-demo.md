# Portfolio Demo Script

This script is the intended 3–4 minute demonstration of the current hotel assistant prototype.

## Starting state

Use the local mock PMS. Start in **Reception → Morning**.

The mock data includes today's arrival for John Martin in room 214, room 214 in a non-ready state, an open housekeeping incident, and normal room/guest data.

The web UI displays the running application version in the connection status. For this release it should show **v0.1.1**. Static demo assets are served without caching so a new release cannot silently reuse an older JavaScript or CSS file.

## Act 1 — Reception

### 1. Today's arrivals

Ask:

> Who is checking in today?

Expected behavior:

- the deterministic parser maps the request to `GET_ARRIVALS`;
- the assistant returns the actual arrival record, including **John Martin**, **room 214**, reservation **r1**, and its status/dates;
- the UI displays the resolved command below the response.

### 2. Room readiness

Ask:

> Which rooms are not ready for today's arrivals?

Expected behavior:

- the assistant identifies arrival rooms that are not ready;
- the response identifies **room 214 — DIRTY** in the supplied demo data.

### 3. Room problem

Ask:

> The air conditioning in room 214 isn't working.

Expected behavior:

- the parser identifies an incident request;
- the assistant prepares `CREATE_INCIDENT` with room `214`, type `MAINTENANCE`, and the original description;
- Reception is authorized to report the incident;
- the write operation requires confirmation;
- confirm the operation;
- the response identifies the newly created incident and its room/type/status.

### 4. Permission boundary

Still as Reception, attempt a housekeeping-only write:

> Mark room 214 clean.

Expected behavior:

- Reception is denied before execution;
- the response explains that the operation requires Housekeeping or Management permission.

This is an intentional failure case: the demo should show the system pushing back rather than only succeeding.

## Act 2 — Housekeeping

Switch to **Housekeeping**.

### 5. Rooms requiring attention

Ask:

> Which rooms are not ready?

Expected behavior:

- the assistant returns rooms whose status is not READY, including room 214 until the clean operation is completed.

### 6. Controlled room update

Ask:

> Mark room 214 clean.

Expected behavior:

- the command is authorized;
- confirmation is requested;
- confirm the operation;
- room 214 becomes READY in the mock PMS;
- the UI shows the room state transition and the audit result.

Optional demonstration:

Start the same write and answer `No` to the confirmation. The room must remain unchanged.

## Act 3 — Management

Switch to **Management**.

### 7. Operational summary

Ask:

> Show operational summary.

Expected behavior:

The response should include the core operational metrics already calculated by `PMSService`, including arrivals, departures, occupancy, available rooms, rooms requiring attention, and open incidents.

### 8. Approved automation

Ask:

> List automations.

Then inspect the available **Morning Arrival Check** automation.

If it is disabled, enable it through the normal confirmation flow before running it.

Then ask:

> Run the morning arrival check.

Expected behavior:

- Management is authorized;
- confirmation is required;
- the predefined automation checks today's arrival rooms;
- execution is persisted and audited;
- the result reports which arrival rooms require attention.

## Technical story to explain while recording

The demonstration should make these points visible:

1. Natural language is interpreted into a constrained command.
2. The deterministic command registry remains authoritative.
3. Permissions are checked before execution.
4. Mutating operations require explicit confirmation.
5. PMS access goes through `PMSService` and `PMSInterface`.
6. Automation is predefined and deterministic rather than AI-generated.
7. The optional LLM can interpret language, but it never receives execution authority.
8. The displayed application version lets the reviewer verify which build is actually running.

## Definition of a successful recording

The viewer should see:

```text
Reception → arrivals with details → room readiness with room/status
        → report AC incident → confirmation → successful incident creation
        → denied room-clean write
        ↓
Housekeeping → room clean → confirmation → READY
        ↓
Management → summary → approved automation
```

The recording should show at least one successful write and one blocked operation.
