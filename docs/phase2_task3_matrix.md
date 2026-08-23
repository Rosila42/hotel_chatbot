# Phase 2 — Task 3: Parser Test Matrix

The parser matrix is maintained against the authoritative command registry.

The core invariant is:

```text
set(matrix command names) == set(CommandRegistry command names)
```

This ensures every command has at least one deterministic natural-language path and that parser output cannot introduce commands outside the catalog.

The matrix also verifies unknown text returns `None` and that `CommandRequest` contains only name/parameter data, leaving authorization, validation, confirmation, and execution to the router.
