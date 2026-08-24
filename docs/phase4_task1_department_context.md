# Phase 4 Task 1 — Department Context

## Scope

Introduce a small department-context layer without duplicating PMS commands by department or shift.

## Invariants

- Reception remains one department with `morning`, `afternoon`, and `night` context.
- Housekeeping and Management have no artificial shift requirement.
- Shared command authorization remains in the core permission/command system.
- Department classes expose context and UX hints only; they do not execute PMS operations.
- Shift hints are copied before being returned so callers cannot mutate global definitions.

## Implemented

- `departments.base.DepartmentContext`
- normalized `Shift` parsing
- authoritative `ReceptionChat` context
- Housekeeping and Management context objects
- department context tests
- catalog-aligned Reception suggestions
