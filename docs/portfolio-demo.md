# Portfolio Demo Script

This script is the intended 3–4 minute demonstration of the current hotel assistant prototype.

## Starting state

Use the local mock PMS. Start in **Reception → Morning**.

The mock data includes today's arrivals, room 214 in a non-ready state, an open incident, and normal room/guest data.

## Act 1 — Reception

### 1. Today's arrivals

Ask:

> Who is checking in today?

Expected behavior:

- the deterministic parser maps the request to `GET_ARRIVALS`;
- the assistant returns today's arrivals;
- the UI displays the resolved command below the response.

### 2. Room readiness

Ask:

> Which rooms are not ready for today's arrivals?

Expected behavior:

- the assistant identifies arrival rooms that are not ready;
- the response should highlight room 214 in the supplied demo data.

### 3. Room problem

Ask:

> The air conditioning in room 214 isn't working.

Expected behavior:

- the parser identifies an incident request;
- the assistant prepares `CREATE_INCIDENT`;
- the write operation requires confirmation;
- confirm the operation.

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

- the assistant returns rooms whose status is not READY.

### 6. Controlled room update

Ask:

> Mark room 214 clean.

Expected behavior:

- the command is authorized;
- confirmation is requested;
- confirm the operation;
- room 214 becomes READY in the mock PMS.

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

## Definition of a successful recording

The viewer should see:

```text
Reception → arrivals → room problem → permission denial
        ↓
Housekeeping → room clean → confirmation
        ↓
Management → summary → approved automation
```

The recording should show at least one successful write and one blocked operation.