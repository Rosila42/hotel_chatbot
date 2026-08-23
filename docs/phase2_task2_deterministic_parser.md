# Phase 2 — Task 2: Deterministic Parser Improvements

## Status

Implemented on branch: `phase2/task2-deterministic-parser`

Baseline: merged Phase 2 Task 1, parser → `CommandRequest` contract.

## Purpose

Task 2 improves deterministic natural-language coverage without changing the parser contract or the trusted execution pipeline.

The parser remains an interpretation-only component:

```text
raw text
   ↓
DeterministicParser
   ↓
CommandRequest | None
   ↓
ChatRouter
   ↓
permission → validation → confirmation → execution
```

## Improvements

### Arrival and departure language

The parser now recognizes common hotel phrasing including:

- arrivals / arriving
- departures / leaving
- check in / checking in / check-ins
- check out / checking out / check-outs
- expected guests

Relative dates are supported for these read requests:

- today: current injected date
- tomorrow: current date + 1 day
- yesterday: current date - 1 day
- explicit ISO date: `YYYY-MM-DD`

### Guest search

Guest lookup now accepts natural forms such as:

```text
find Maria Rossi
search guest Maria Rossi
look up guest Maria Rossi
```

The extracted guest name is preserved in its original casing.

### Reservation lookup

Both `reservation` and `booking` vocabulary are accepted.

Reservation identifiers preserve their original casing, for example:

```text
booking ABC-123
```

produces:

```python
CommandRequest(
    "GET_RESERVATION",
    {"reservation_id": "ABC-123"},
)
```

A reservation can also be requested by guest name:

```text
reservation for Maria Rossi
```

### Room operations

Room-number extraction now supports forms such as:

```text
room 214
room number 214
```

Room-status questions cover states such as:

```text
ready
clean
dirty
cleaning
available
occupied
vacant
out of order
```

Explicit clean actions remain separate:

```text
mark room 214 clean
set room 214 clean
```

### Incident precedence

Explicit incident reporting takes precedence over passive room-state words.

Therefore:

```text
room 214 is dirty
```

remains a read:

```text
GET_ROOM_STATUS
```

while:

```text
report a dirty room 214
```

becomes:

```text
CREATE_INCIDENT
```

This is an important parser precedence rule because the two requests contain overlapping language but have different operational consequences.

### Operational summary aliases

The parser recognizes:

- operational summary
- hotel summary
- daily summary
- daily ops
- operations summary
- today's summary

### FAQ aliases

The parser now recognizes common FAQ topics including:

- breakfast
- check-in/check-out time
- Wi-Fi / internet
- hotel policy
- cancellation policy
- parking

The parser still produces `FAQ_SEARCH`; it does not generate the answer itself.

## Design constraints preserved

Task 2 deliberately does not introduce:

- fuzzy matching libraries;
- embeddings;
- vector search;
- an LLM;
- semantic similarity models;
- authorization logic;
- PMS access;
- command execution;
- confirmation decisions.

Those remain outside this parser's responsibility.

## Why relative dates belong here

Date interpretation is part of converting natural language into command parameters. The parser therefore resolves only simple deterministic relative expressions and explicit ISO dates.

The authoritative command schema remains responsible for structural validation after authorization.

## Test matrix

The parser tests now cover:

- original Task 1 contract behavior;
- arrival aliases;
- departure aliases;
- relative dates;
- ISO dates;
- direct guest search;
- guest-name extraction;
- booking vocabulary;
- reservation-by-guest lookup;
- room status;
- passive dirty-room reads;
- mark-room-clean operations;
- housekeeping incident creation;
- operational summaries;
- FAQ aliases;
- automation precedence.

## Boundary with future LLM parsing

The deterministic parser remains one implementation of the `Parser` protocol.

A future LLM parser must produce the same `CommandRequest | None` contract. It must not bypass the router.

```text
                Parser
                 │
        ┌────────┴────────┐
        ▼                 ▼
DeterministicParser     LLMParser
        │                 │
        └────────┬────────┘
                 ▼
          CommandRequest
                 ▼
             ChatRouter
```

## Task 2 completion criterion

Task 2 is complete when deterministic recognition covers the established command vocabulary and common hotel phrasing, precedence rules are regression-tested, and no trusted execution responsibility has moved into the parser.
