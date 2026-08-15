# Hotel PMS Chatbot V2 — Implementation Plan

## Status

Planning document only. No application implementation is authorized by this document.

## 1. Product Objective

Build a modular chatbot feature that integrates with an existing Hotel PMS/application and provides:

- FAQ
- PMS information access
- PMS operations
- controlled automation
- optional AI/LLM enhancement

The chatbot is not a replacement PMS. The existing PMS remains the system of record.

## 2. Frozen Architectural Principles

1. Deterministic chatbot core; LLM optional.
2. LLM output is untrusted input and must use the same command validation and permission path as deterministic intent recognition.
3. PMS data is authoritative.
4. PMS access is isolated behind `PMSService -> PMSInterface -> PMSAdapter`.
5. V1 uses a mock PMS API adapter for development/demo; direct PMS DB integration is deferred.
6. Reception is one module with morning/afternoon/night shift context.
7. Shared PMS capabilities are implemented once and exposed through permissions rather than duplicated by department.
8. Automation is asynchronous: AutomationService manages definitions; AutomationWorker executes them.
9. V1 automation uses predefined templates, not arbitrary natural-language workflow creation.
10. API is stateless; session/application state is persisted in SQLite/SQLAlchemy.
11. Authentication establishes trusted identity before ChatSession creation.
12. All PMS mutations are auditable and pass through the PMS service layer.
13. PMS failures are explicit operational states, not raw exceptions shown to users.
14. Optional AI uses `AIService -> LLMAdapter -> one concrete provider` only; no provider registry or multi-provider framework in V1.

## 3. Frozen V1 Stack

- Python 3.10+
- FastAPI
- Pydantic
- SQLite
- SQLAlchemy
- APScheduler
- LiteLLM behind a thin `LLMAdapter`
- pytest

Do not add PostgreSQL, Redis, Celery, Kafka, RabbitMQ, LangChain-based application architecture, Kubernetes, or microservices unless explicitly approved after a concrete requirement appears.

## 4. Target V2 Structure

```text
hotel_chatbot/
├── api/
│   ├── routers/
│   └── ...
├── core/
│   ├── session.py
│   ├── router.py
│   ├── intent.py
│   ├── commands.py
│   ├── permissions.py
│   └── ...
├── departments/
│   ├── reception/
│   ├── housekeeping/
│   └── management/
├── services/
│   ├── pms_service.py
│   ├── faq_service.py
│   └── automation_service.py
├── integrations/
│   └── pms/
│       ├── interface.py
│       └── mock_adapter.py
├── ai/
│   ├── ai_service.py
│   └── llm_adapter.py
├── models/
│   ├── commands.py
│   ├── session.py
│   ├── pms.py
│   └── api.py
├── tests/
└── main.py
```

This is a responsibility map, not a requirement to create unnecessary modules.

## 5. Current Prototype Assessment

Repository: `Rosila42/hotel_chatbot`.

The current repository is a prototype with one commit (`first commit`) and multiple implementation generations.

### `base_chatbot.py`

Current responsibilities include UI, DB connection, intent detection, permissions, SQL, PMS operations, message handling, and response formatting.

V2 disposition: **REWRITE/EXTRACT**.

Keep the useful behavior as requirements, but do not preserve the coupling.

### `main_chatbot.py`

Current responsibilities include routing, specialized chat launching, UI/window management, history, and system status.

V2 disposition: **REPLACE WITH CORE ROUTER + SESSION/API STRUCTURE**.

### `reception/morning_chat.py`

Legacy/lightweight reception implementation.

V2 disposition: **REWRITE INTO ONE RECEPTION MODULE WITH SHIFT CONTEXT**.

### `reception/afternoon_chat.py`, `reception/night_chat.py`

Currently incomplete/empty.

V2 disposition: **DELETE/REPLACE**; represent shift as context, not duplicate classes.

### `housekeeping/housekeeping_chat.py`

Currently empty.

V2 disposition: **NEW IMPLEMENTATION**.

### `manager/manager_chat.py`

Contains useful dashboard, room-management, statistics, and operational concepts but is tightly coupled to Tkinter and direct DB access.

V2 disposition: **REWRITE, preserving useful functional requirements**.

### `other/chat.py`, `other/chatp.py`

Prototype/legacy implementations.

V2 disposition: **REVIEW, then remove unless a concrete unique capability is discovered**.

### `simple_test.py`

UI/dependency smoke-test prototype.

V2 disposition: **REMOVE from final architecture; replace with pytest tests**.

### `test_chatbot.py`

Current testing is insufficient for V2.

V2 disposition: **REPLACE/EXPAND into behavioral/unit/integration tests**.

### `__pycache__` / `.pyc`

V2 disposition: **REMOVE from repository and ignore via `.gitignore`**.

## 6. Immediate Security Cleanup

The prototype contains hardcoded database credentials in `main_chatbot.py`.

Before public/portfolio use:

1. remove the credential from source control;
2. rotate the exposed credential;
3. move configuration/secrets to environment or secure configuration.

Do not publish or reuse the exposed credential.

## 7. Proposed Migration Sequence

### Phase 0 — Repository hygiene

- remove tracked bytecode/cache files;
- add/update `.gitignore`;
- remove hardcoded secrets;
- establish configuration strategy;
- create V2 branch (`feat/v2-architecture`).

### Phase 1 — Core extraction

Extract responsibilities from the existing BaseChatbot/MainChatbot prototype into:

- `core/session.py`
- `core/message.py` or equivalent model representation
- `core/router.py`
- `core/intent.py`
- `core/commands.py`
- `core/permissions.py`

The first implementation target is to preserve deterministic chatbot behavior without Tkinter-specific logic.

### Phase 2 — PMS boundary

Implement:

- `PMSInterface`
- `MockPMSAdapter`
- `PMSService`

The mock adapter should expose realistic PMS-like operations required by the command catalog.

No direct PMS DB access in V1.

### Phase 3 — Command registry

Implement a centralized command registry containing only the approved V1 catalog.

Each command must specify:

- name
- category
- parameters
- validation
- permission
- read/write classification
- confirmation requirement
- service handler
- expected response/data policy

### Phase 4 — Departments

Implement:

- Reception with shift context
- Housekeeping
- Management

Department modules should express workflow/context, not duplicate shared PMS commands.

### Phase 5 — Authentication and sessions

Implement a V1 authentication mechanism sufficient for the demo and architecture.

Create trusted identity before creating a ChatSession.

Persist session/message state using SQLite + SQLAlchemy.

### Phase 6 — API

Expose the chatbot through FastAPI.

The API should be stateless and should load/update persisted session state.

At minimum the API should support conversational chat and the underlying structured capability access required by the application.

### Phase 7 — FAQ

Implement deterministic FAQ retrieval using controlled/approved content.

Do not use an LLM for normal FAQ retrieval.

### Phase 8 — Automation

Implement:

- Automation definitions
- predefined templates
- AutomationService
- APScheduler-based AutomationWorker
- persistent execution history/state
- scheduled triggers
- explicit partial-failure handling

Do not implement arbitrary workflow authoring in V1.

### Phase 9 — Reliability and audit

Implement:

- PMS timeouts
- safe limited retries where applicable
- clear failure responses
- no false success claims
- centralized mutation audit
- automation execution audit/history

### Phase 10 — Tests

Build pytest coverage for:

- command recognition
- ambiguity handling
- permissions
- confirmation flow
- PMS service behavior
- adapter normalization
- API behavior
- authentication/session behavior
- FAQ
- automation execution
- partial failure
- audit logging

### Phase 11 — Optional AI

Only after deterministic functionality is stable.

Implement:

`AIService -> LLMAdapter -> one concrete provider`.

Candidate first AI feature should be selected based on measured usefulness, cost, latency, and hallucination risk.

AI must return one structured command and use the same command registry/validation/permission path as deterministic intent recognition.

### Phase 12 — Demo and portfolio

Prepare:

- realistic demo data
- demonstration scenario
- screenshots
- short demo video
- architecture documentation
- API documentation
- testing documentation
- portfolio/LinkedIn materials

## 8. V1 Command Catalog

### System

- `HELP`
- `GET_SYSTEM_STATUS`

### PMS — Guest/Reservations

- `SEARCH_GUEST`
- `GET_RESERVATION`
- `GET_ARRIVALS`
- `GET_DEPARTURES`

### PMS — Rooms

- `GET_ROOM_STATUS`
- `MARK_ROOM_CLEAN`

### PMS — Incidents

- `GET_INCIDENTS`
- `CREATE_INCIDENT`
- `RESOLVE_INCIDENT`

### PMS — Operations

- `GET_OPERATIONAL_SUMMARY`

### FAQ

- `FAQ_SEARCH`

### Automation

- `LIST_AUTOMATIONS`
- `ENABLE_AUTOMATION`
- `DISABLE_AUTOMATION`
- `RUN_AUTOMATION`
- `GET_AUTOMATION_STATUS`
- `GET_AUTOMATION_HISTORY`

`CONFIRM` and `CANCEL` are session/action state controls, not ordinary PMS commands.

## 9. Commands Explicitly Deferred from V1

Do not implement unless a concrete requirement is approved:

- bulk room updates
- generic room-detail editing
- room out-of-service operations
- generic room-status mutation
- reservation-note editing
- housekeeping task subsystem
- operational trend analytics
- arbitrary automation authoring
- full reservation creation/cancellation workflows
- payment/billing operations
- multi-property management
- direct PMS database integration
- multi-provider AI framework

## 10. Core Command/Service Rule

If a command touches shared PMS data, implement one shared capability and control access through permissions.

Example:

`GET_ROOM_STATUS` is not a Reception command and a Housekeeping command. It is one PMS capability available to authorized roles.

If an operation is a chatbot-introduced workflow concept rather than a PMS primitive, it may remain department-owned or automation-owned.

## 11. PMS Composition Rule

The chatbot core must not contain business composition loops over PMS entities.

Example:

`GET_ROOM_STATUS(filter=NOT_READY_ARRIVALS)` should invoke PMSService logic that composes arrivals and room state, not chatbot code that manually loops over PMS results.

The adapter translates vendor-specific API semantics; PMSService owns application-level composition.

## 12. Data Minimization

Permission and response data policy are separate.

Each command should explicitly define which fields are allowed in its response.

Sensitive data must not be exposed merely because the PMS stores it.

At minimum consider:

- government ID
- passport information
- payment information
- credentials
- unnecessary sensitive notes

When cloud AI is eventually enabled, minimize/redact before data reaches the external model.

## 13. Confirmation

Potential write risk classes:

- low risk: e.g. `MARK_ROOM_CLEAN`
- medium risk: e.g. `CREATE_INCIDENT`
- high/variable risk: e.g. `RUN_AUTOMATION`

The command specification must define which actions require a pending confirmation state.

Scheduled execution of an already authorized automation must not require manual confirmation each time.

## 14. AI Safety Rule

AI-derived intent is untrusted input.

The path is always:

AI → one structured command → registry → validation → permission → service → PMS/automation.

No alternate AI execution path.

## 15. Acceptance Criteria for V2 Planning

The implementation plan is acceptable only if it:

1. maps every relevant prototype component to a V2 responsibility;
2. explicitly identifies obsolete/inconsistent prototype files;
3. gives a small, reviewable migration sequence;
4. does not introduce unapproved infrastructure;
5. includes authentication, session persistence, automation worker/state, resilience, audit, and data minimization;
6. preserves the deterministic-core principle;
7. keeps AI optional and isolated;
8. keeps the existing PMS authoritative;
9. includes test strategy for all critical behavior;
10. clearly separates V1 from future work.

## 16. Approval Gate

This document is a planning artifact.

Implementation must not be inferred from its existence.

Implementation begins only after explicit human approval.
