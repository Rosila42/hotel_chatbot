# Hotel PMS Chatbot V2

A lightweight, local web application that adds a conversational and automation layer to an existing hotel PMS.

V2 is being developed on `main`.

## What it is

This project is **not a replacement PMS**. The PMS remains the system of record.

The application provides:

- deterministic hotel FAQ;
- PMS information access;
- controlled PMS operations;
- predefined automation workflows;
- role-based permissions;
- persistent sessions and audit history;
- an optional AI layer that is not required for core operation.

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

The package bundles the Python application and its core dependencies. SQLite data is stored under the user's Linux application-data directory, not inside the installed program directory.

## Local web application

The V2 product runs locally as a small FastAPI web service and is opened in a normal browser.

```text
Browser
   ↓
FastAPI
   ↓
Chat Core
   ├── FAQ
   ├── PMS Service → PMS Adapter
   └── Automation Worker
```

SQLite is used for local persistence. No MySQL, PostgreSQL, Redis, Celery, Docker, or cloud service is required for the V2 demo.

## Ubuntu package build

The repository contains a GitHub Actions workflow that builds the Ubuntu `.deb` package from the V2 branch.

The resulting package can be downloaded from the workflow artifact and installed by double-clicking it in Ubuntu Software.

For development machines, the terminal-based setup remains available:

```bash
sudo apt update
sudo apt install python3.11 python3.11-venv git

git clone https://github.com/Rosila42/hotel_chatbot.git
cd hotel_chatbot
git checkout main
bash install_v2.sh
bash run_v2.sh
```

The developer launcher starts the local server and, on Ubuntu desktops with `xdg-open`, opens:

```text
http://127.0.0.1:8000/app/
```

The FastAPI documentation is available at:

```text
http://127.0.0.1:8000/docs
```

## Demo users

The V2 demo currently uses simple local bearer tokens:

```text
Reception:     demo-reception-token
Housekeeping:  demo-housekeeping-token
Management:    demo-manager-token
```

These are demonstration credentials only. Production deployments should federate identity with the host PMS/application.

## Verification

Developers can run:

```bash
bash verify_v2.sh
```

This performs the pytest suite, Python compilation check, and FastAPI import check.

## Optional AI

AI is deliberately separated from the deterministic core.

The core installation does **not** require an LLM provider.

When AI work begins, install the optional dependency set:

```bash
python -m pip install -r requirements-ai.txt
```

The AI path remains behind `AIService` and a thin `LLMAdapter`.

## Development status

Completed V2 foundation:

- FastAPI API
- local web UI
- native Ubuntu packaging workflow
- SQLite persistence
- authentication/identity boundary
- command registry
- deterministic intent routing
- mock PMS adapter
- automation service and worker
- confirmation workflow
- audit logging
- PMS resilience policy
- pytest coverage
- optional AI boundary

Remaining product work includes deeper FAQ content, richer department workflows, production authentication integration, a real PMS adapter, and optional AI features.

## Current verified baseline
The latest verified baseline for this project is documented in [docs/verification/2026-08-23-postmerge.md](docs/verification/2026-08-23-postmerge.md).
