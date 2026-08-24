# Hotel PMS Chatbot V2

A lightweight local web application that adds a deterministic conversational and automation layer to an existing hotel PMS.

## What it is

This project is **not a replacement PMS**. The PMS remains the system of record.

The application provides:

- deterministic hotel FAQ and intent routing;
- PMS information access;
- controlled PMS operations;
- predefined automation workflows;
- role-based permissions;
- persistent sessions and audit history;
- an optional AI parsing boundary that is not required for core operation.

The deterministic command pipeline is authoritative. An optional LLM may translate free text into a constrained `CommandRequest`, but authorization, validation, confirmation, and execution remain inside the deterministic core.

## Runtime architecture

```text
Browser / Desktop launcher
          ↓
        FastAPI
          ↓
  Deterministic Chat Router
    ├── Command Registry
    ├── Permission Service
    ├── Confirmation Gate
    └── Command Executor
          ↓
      PMS Service
          ↓
     PMS Interface
      ├── Mock Adapter
      └── Real REST Adapter (prototype)
```

SQLite is used for local persistence. Alembic owns the database schema and is applied automatically during application startup.

## Normal-user experience on Ubuntu

The intended distribution format is a native Debian package (`.deb`). A non-technical user should not need a terminal.

```text
Download Hotel Chatbot V2 .deb
            ↓
Double-click the file
            ↓
Ubuntu Software → Install
            ↓
Open Applications → Hotel Chatbot V2
            ↓
Browser opens automatically
```

The package bundles the Python application, web assets, and Alembic migration resources. SQLite data is stored under the user's Linux application-data directory, not inside the installed program directory.

## Development

The main development branch is `main`.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-v2.txt
PYTHONPATH=. pytest -v
```

The local launcher starts the application at:

```text
http://127.0.0.1:8000/app/
```

FastAPI documentation is available at:

```text
http://127.0.0.1:8000/docs
```

For a convenience desktop-style launcher on Ubuntu:

```bash
bash install_v2.sh
```

## Demo users

The V2 demo currently uses local bearer tokens:

```text
Reception:      demo-reception-token
Housekeeping:   demo-housekeeping-token
Management:     demo-manager-token
```

These are demonstration credentials only. Production deployments should federate identity with the host PMS/application and must not expose demo credentials on untrusted networks.

## PMS integration

Development defaults to the in-memory/mock PMS adapter.

A REST-based `RealPMSAdapter` exists behind the `PMSInterface` boundary and can be selected with:

```bash
export HOTEL_CHATBOT_PMS_ADAPTER=real
```

The current real adapter is an integration skeleton: its transport, request tracing, retry policy, and data mapping are implemented, but its OAuth token exchange is still a placeholder. It is not yet a production PMS connector.

## Optional AI

The core installation does **not** require an LLM provider.

The optional AI boundary only translates user text into a constrained command request. The deterministic router remains responsible for authorization, parameter validation, confirmation, and execution.

## Verification

Run the repository verification script:

```bash
bash verify_v2.sh
```

Or run the exact test command directly:

```bash
PYTHONPATH=. pytest -v
```

The CI workflow also checks JavaScript syntax with Node.js before the package workflow builds the Ubuntu installer.

## Development status

The V2 foundation is implemented, including:

- FastAPI API;
- local web UI;
- Ubuntu packaging workflow;
- SQLite persistence and Alembic migrations;
- authentication/identity boundary;
- command registry and deterministic parser;
- mock PMS adapter;
- automation service and worker;
- confirmation workflow with concurrency protection;
- audit logging;
- PMS resilience policy;
- integration and unit test coverage;
- optional AI parser boundary.

Remaining product work is primarily deeper hotel-specific workflows, production authentication integration, production PMS authentication/integration, richer FAQ content, and optional AI features.
