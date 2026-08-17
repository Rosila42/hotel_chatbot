# Hotel PMS Chatbot

V2 development is on `feat/v2-architecture`.

The default `main` branch remains the original prototype baseline.

## V2 quick start on Ubuntu

### 1. Get the V2 branch

```bash
git clone https://github.com/Rosila42/hotel_chatbot.git
cd hotel_chatbot
git checkout feat/v2-architecture
```

### 2. Create the virtual environment

Python 3.11 is recommended.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

If the machine only provides `python3`, use:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install the V2 core

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements-v2.txt
```

The deterministic V2 core does **not** require an LLM.

Optional AI dependencies are isolated in:

```bash
python -m pip install -r requirements-ai.txt
```

Do this only when the optional AI layer is actually being configured.

### 4. Verify V2

```bash
bash verify_v2.sh
```

This runs the pytest suite, compiles the source tree, and imports the FastAPI application.

### 5. Run the API

```bash
bash run_v2.sh
```

Or, with the virtual environment already activated:

```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000/docs
```

### 6. Demo authentication tokens

These are development-only tokens:

```text
Reception:     demo-reception-token
Housekeeping:  demo-housekeeping-token
Manager:       demo-manager-token
```

For example:

```bash
curl -H 'Authorization: Bearer demo-reception-token' \
  http://127.0.0.1:8000/capabilities
```

Do not use the demo tokens in production.

## Data

V2 uses SQLite by default and creates:

```text
hotel_chatbot_v2.db
```

The database file is ignored by Git.

## Architecture

The deterministic application is the core. The LLM is optional.

```text
Chat UI
  ↓
FastAPI
  ↓
Authentication / Session
  ↓
Core Router / Command Registry
  ↓
Services
  ↓
PMS Adapter / Automation
```

The PMS remains the system of record. Direct PMS database integration is not part of V1.
