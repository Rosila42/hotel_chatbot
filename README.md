# Hotel PMS Chatbot V2

A lightweight, local web application that adds a conversational and automation layer to an existing hotel PMS.

V2 is being developed on `feat/v2-architecture`.

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

## Ubuntu setup

Recommended: Python 3.11+

```bash
sudo apt update
sudo apt install python3.11 python3.11-venv git
```

Clone the repository and switch to V2:

```bash
git clone https://github.com/Rosila42/hotel_chatbot.git
cd hotel_chatbot
git checkout feat/v2-architecture
```

Install the core application:

```bash
bash install_v2.sh
```

Run it:

```bash
bash run_v2.sh
```

The launcher starts the local server and, on Ubuntu desktops with `xdg-open`, opens:

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

Run:

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
