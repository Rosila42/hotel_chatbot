from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


TEST_DB = Path(f"/tmp/hotel-chatbot-test-{os.getpid()}.db")
os.environ["HOTEL_CHATBOT_TEST_DB"] = str(TEST_DB)
if TEST_DB.exists():
    TEST_DB.unlink()

from main import app  # noqa: E402
from storage import Base, engine  # noqa: E402

Base.metadata.create_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def reception_headers():
    return {"Authorization": "Bearer demo-reception-token"}


@pytest.fixture
def housekeeping_headers():
    return {"Authorization": "Bearer demo-housekeeping-token"}


@pytest.fixture
def manager_headers():
    return {"Authorization": "Bearer demo-manager-token"}
