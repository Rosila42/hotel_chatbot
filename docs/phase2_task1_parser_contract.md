# Phase 2 — Task 1: Parser → `CommandRequest` Contract

## Status

**Implemented on branch:** `phase2/task1-parser-contract`

**Baseline:** Task 3 merge commit `80f3af25919aaa3607a90d2437ec8f425a23ad9e`

## Purpose

Task 1 establishes the boundary between natural-language interpretation and the trusted deterministic command pipeline.

The parser is an interpretation component. Its only responsibility is to transform user text into a `CommandRequest` or return no match.

```text
raw text
   ↓
Parser
   ↓
CommandRequest | None
   ↓
ChatRouter
   ↓
permission → validation → confirmation → execution
```

## Contract

The parser contract is represented by the `Parser` protocol in `core/parser.py`:

```python
class Parser(Protocol):
    def parse(self, text: str) -> CommandRequest | None:
        ...
```

A parser implementation MUST:

1. Consume raw user text.
2. Return `CommandRequest(name, parameters)` for a recognized request.
3. Return `None` when the request cannot be mapped to a supported capability.
4. Produce only command names and parameters defined by the application contract.

A parser implementation MUST NOT:

- authorize the user;
- inspect or manufacture permissions;
- perform confirmation decisions;
- call the PMS;
- call automation services;
- mutate application state;
- execute commands directly.

## Reference implementation

`DeterministicParser` is the current production parser implementation for Phase 2 Task 1.

It contains the existing rule-based natural-language interpretation previously embedded in `ChatRouter`. The behavior is intentionally kept simple and deterministic while the parser boundary is established.

The parser receives an injectable date provider so date-dependent requests remain deterministic in tests.

## Router responsibility

`ChatRouter` now depends on the parser interface rather than owning parsing rules.

The router remains the trusted execution policy boundary:

```text
Parser
  ↓
CommandRequest
  ↓
Command lookup
  ↓
Authorization
  ↓
Structural validation
  ↓
Confirmation
  ↓
CommandExecutor
```

This preserves the Task 3 security invariant that authorization occurs before confirmation and before execution.

## Future parser implementations

Future parsers must implement the same interface.

```text
             ┌──────────────────────┐
             │      Parser          │
             │ parse(text)          │
             └──────────┬───────────┘
                        │
              ┌─────────┴─────────┐
              ▼                   ▼
   DeterministicParser         LLMParser
              │                   │
              └─────────┬─────────┘
                        ▼
                 CommandRequest
                        ▼
                   ChatRouter
```

An LLM parser therefore becomes another interpretation adapter, not another execution architecture.

## Current precedence rule

Specialized automation phrases are recognized before generic arrival/departure language so that:

```text
run morning arrival check
```

maps to:

```python
CommandRequest(
    "RUN_AUTOMATION",
    {"automation_id": "MORNING_ARRIVAL_CHECK"},
)
```

rather than `GET_ARRIVALS`.

The parser also explicitly recognizes incident-list requests before the generic incident-creation rule. This prevents:

```text
show open incidents
```

from being interpreted as `CREATE_INCIDENT`.

## Validation boundary

The parser does not perform full command-schema validation.

For example, the parser may produce a `CommandRequest` whose parameters are structurally incomplete. The command definition's Pydantic model remains responsible for authoritative structural validation inside `ChatRouter` after authorization.

This distinction is intentional:

```text
Parser = interpretation
CommandDefinition = parameter contract
ChatRouter = policy
CommandExecutor = execution
```

## Test requirements

The Task 1 test suite verifies:

- recognized text produces `CommandRequest`;
- unknown text returns `None`;
- parser output contains no authorization/execution behavior;
- automation precedence is preserved;
- incident-list intent is distinct from incident creation;
- date-dependent parsing can be tested deterministically.

## Task 1 completion criterion

Phase 2 Task 1 is complete when the parser interface is explicit, the deterministic parser implements it, the router consumes the interface, and the tests establish the behavior that future parsers must preserve.
