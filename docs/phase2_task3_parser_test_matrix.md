# Phase 2 — Task 3: Parser Test Matrix

## Status

Implemented on branch `phase2/task3-parser-test-matrix`.

## Purpose

Task 3 makes parser coverage measurable against the authoritative `CommandRegistry` instead of relying on a growing collection of isolated examples.

The test matrix has one representative natural-language input for every command currently defined by the registry.

## Coverage contract

The matrix must satisfy:

```text
set(parser matrix command names)
    ==
set(authoritative registry command names)
```

This prevents two failure modes:

1. a command exists but has no deterministic natural-language path;
2. the parser starts emitting a command that is not part of the authoritative catalog.

## Current command coverage

All 19 registry commands have matrix coverage:

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

## Additional invariants

The matrix also verifies that:

- unknown text returns `None`;
- parser output contains only `CommandRequest` data;
- permission, confirmation, and identity information cannot be represented by parser output;
- the parser command set remains aligned with the authoritative registry.

## Security boundary

This task does not move authorization or execution into the parser.

The parser remains:

```text
raw text → CommandRequest | None
```

The trusted router remains:

```text
CommandRequest
    ↓
authorization
    ↓
validation
    ↓
confirmation
    ↓
execution
```

## Why this matrix matters

Task 2 improved deterministic language coverage. Task 3 converts that improvement into a maintainable regression contract. Future parser implementations can be evaluated against the same command catalog and expanded with additional examples without changing the execution architecture.
