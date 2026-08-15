# Hotel PMS Chatbot V2 — Implementation Plan

## Status

Planning document only. No application implementation is authorized by this document.

## Product Objective

Build a modular chatbot feature that integrates with an existing Hotel PMS/application and provides FAQ, PMS information access, PMS operations, controlled automation, and optional AI enhancement. The chatbot is not a replacement PMS.

## Frozen principles

- Deterministic core; LLM optional.
- AI output is untrusted and uses the same command/validation/permission path as deterministic intent.
- PMS remains authoritative.
- PMS access is `PMSService -> PMSInterface -> PMSAdapter`.
- V1 uses a mock PMS API adapter; direct PMS DB integration is deferred.
- Reception is one module with shift context.
- Shared PMS capabilities are not duplicated by department.
- Automation is asynchronous with AutomationService + AutomationWorker.
- V1 automation uses predefined templates.
- API is stateless with SQLite/SQLAlchemy persistence.
- Authentication establishes trusted identity.
- PMS mutations are audited.
- PMS failures are handled explicitly.
- Optional AI uses `AIService -> LLMAdapter -> one provider` with no provider registry in V1.

## V1 stack

Python 3.10+, FastAPI, Pydantic, SQLite, SQLAlchemy, APScheduler, LiteLLM behind a thin LLMAdapter, pytest.

## Target structure

```text
hotel_chatbot/
├── api/
├── core/
├── departments/
├── services/
├── integrations/
├── ai/
├── models/
├── tests/
├── docs/
└── main.py
```

## Prototype migration

- `base_chatbot.py`: rewrite/extract; preserve useful behavior, remove UI/DB/intent coupling.
- `main_chatbot.py`: replace with router/session/API structure.
- Reception morning/afternoon/night: consolidate into one Reception module with shift context.
- Housekeeping: new V2 implementation.
- Manager: rewrite preserving useful dashboard/operational requirements.
- Legacy `other/*`: remove unless a unique capability is proven.
- Existing smoke tests: replace/expand with pytest behavior tests.
- Remove tracked cache/bytecode artifacts.

## Security

The prototype contains hardcoded DB credentials; before public use, remove and rotate them and move configuration to environment/secure configuration.

## Migration sequence

1. Repository hygiene and branch setup.
2. Core extraction.
3. PMS interface, mock adapter, and PMSService.
4. Centralized command registry.
5. Departments.
6. Authentication and persistent sessions.
7. FastAPI.
8. Deterministic FAQ.
9. Automation definitions, templates, worker, persistence, execution history.
10. Resilience and audit.
11. Tests.
12. Optional AI.
13. Demo/portfolio assets.

## Acceptance criteria

The implementation must remain deterministic without AI, keep PMS authoritative, keep shared PMS capabilities single-sourced, preserve authentication/permission boundaries, persist sessions and automation state, audit mutations, and keep AI optional.
