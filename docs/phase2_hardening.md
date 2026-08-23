# Hotel PMS Chatbot V2 — Runtime Hardening

This pass addresses confirmed runtime risks from the 2026-08-23 project reviews:

- SQLite write contention and request transaction boundaries
- duplicate confirmation execution
- automation failure propagation
- automation enabled-state consistency
- overlapping automation runs
- parser/service room-filter compatibility
- mock incident ID generation
- graceful worker shutdown
- safe default network binding
- desktop launcher UX
- shift transcript/session UX

## Deliberately deferred

`Base.metadata.create_all()` is not a schema migration system. Alembic will be introduced before an installed database needs a versioned schema upgrade. No schema-changing migration is included in this pass.

Event-driven automation is not added speculatively. When event triggers become an implementation requirement, the automation schema will use an explicit trigger discriminator rather than overloading `schedule`.

## Invariants

1. A pending confirmation can be claimed by at most one request.
2. Request-level audit persistence can share the request transaction.
3. Automation failures become `ResultKind.FAILED`.
4. Manual and scheduled automation runs enforce the same enabled-state policy.
5. A given automation cannot overlap with another run in the single-process runtime.
6. Parser and PMS service use the same room-filter vocabulary.
7. Network exposure is opt-in when using demo credentials.
8. Scheduler shutdown waits for active jobs to complete.
