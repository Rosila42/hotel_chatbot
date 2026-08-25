# Hotel PMS Staff Assistant V2

A professional prototype of a hotel staff assistant that puts a conversational interface in front of PMS operations without giving an AI model authority to execute them.

## What it demonstrates

The prototype is built around a simple principle:

> **Natural language at the front. Deterministic operations underneath.**

Reception, Housekeeping, and Management can use the same hotel operations engine while permissions and confirmation rules remain centralized.

The PMS remains the system of record. The application is a staff-assistance layer, not a replacement PMS.

## Portfolio demo

The demo follows one simulated hotel morning:

```text
Reception
   ↓
arrivals + room readiness
   ↓
incident handling
   ↓
Housekeeping
   ↓
room status update
   ↓
Management
   ↓
operational summary + approved automation
```

Start the local application and use the **Reception — Morning** mode.

The complete scripted workflow is in [`docs/portfolio-demo.md`](docs/portfolio-demo.md).

The demo deliberately includes both successful operations and a permission/confirmation boundary so the safety architecture is visible rather than only described.

## Architecture

```text
                    User
                     │
             natural-language input
                     │
        ┌────────────┴────────────┐
        │                         │
 Deterministic parser       Optional LLM parser
        │                         │
        └────────────┬────────────┘
                     │
              CommandRequest
                     │
              Command Registry
                     │
                Permissions
                     │
                Validation
                     │
             Confirmation Gate
                     │
               Command Executor
                     │
                PMS Service
                     │
              PMS Interface
               ┌─────┴─────┐
               │           │
           Mock PMS   REST prototype
```

The LLM, when enabled, is an **interpreter only**. It translates free text into a constrained `CommandRequest`. It does not authorize, validate, confirm, or execute PMS operations.

Predefined automation follows the same deterministic principle. The current prototype provides template-driven automation rather than AI-generated arbitrary multi-step workflows.

## Hotel roles

### Reception

Reception uses the assistant for arrivals, departures, room readiness, guest/reservation lookup, incidents, FAQs, and shift-oriented suggestions.

### Housekeeping

Housekeeping focuses on rooms requiring attention, room status, incidents, and controlled room-status updates.

### Management

Management receives operational summaries and can inspect and run approved automation.

All roles use the same command engine. Department and shift context only shape what is most useful to see and suggest.

## Demo data

The mock PMS provides deterministic hotel data for local demonstrations, including guests, reservations, room states, and an open incident. The demo is designed to work without connecting to a real PMS.

## Running locally

Python 3.12 is recommended.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-v2.txt
PYTHONPATH=. pytest -v
```

Start the application:

```bash
bash run_v2.sh
```

Open:

```text
http://127.0.0.1:8000/app/
```

FastAPI documentation is available at:

```text
http://127.0.0.1:8000/docs
```

Ubuntu packaging is also available through `install_v2.sh` and the Debian packaging workflow.

## Demo users

The local demo uses development-only bearer tokens:

```text
Reception:      demo-reception-token
Housekeeping:   demo-housekeeping-token
Management:     demo-manager-token
```

These credentials are intentionally limited to the local prototype and must not be used for production deployments.

## PMS integration

Development uses the in-memory mock PMS adapter.

A REST-based `RealPMSAdapter` exists behind the `PMSInterface` boundary and can be selected with:

```bash
export HOTEL_CHATBOT_PMS_ADAPTER=real
```

The real adapter is an integration skeleton. Transport, tracing, retry policy, and data mapping are implemented, but its OAuth token exchange remains a placeholder.

## Optional AI

The core system does not require an LLM provider.

When enabled, AI only performs natural-language interpretation. The deterministic core remains authoritative for permissions, validation, confirmation, and execution.

## Verification

Use the repository verification script:

```bash
bash verify_v2.sh
```

Or run the exact test command:

```bash
PYTHONPATH=. pytest -v
```

CI also checks JavaScript syntax before building the Ubuntu package.

## What is intentionally out of scope

This is a professional prototype, not a production hotel SaaS platform.

The following are deliberately deferred:

- production identity federation;
- production PMS OAuth/integration;
- public multi-tenant deployment;
- multi-PMS vendor support;
- AI-generated arbitrary workflows;
- enterprise distributed infrastructure.

Those can be evaluated later against real requirements rather than built speculatively.

## Project status

The V2 foundation is implemented and the current work is focused on productization of the hotel workflows: a coherent staff experience, realistic demo flow, useful UI presentation, and portfolio documentation.
