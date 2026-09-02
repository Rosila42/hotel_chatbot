from __future__ import annotations

import atexit
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


TEST_DB = Path(f"/tmp/hotel-chatbot-test-{os.getpid()}.db")
os.environ["HOTEL_CHATBOT_TEST_DB"] = str(TEST_DB)
for path in (TEST_DB, Path(f"{TEST_DB}-wal"), Path(f"{TEST_DB}-shm")):
    if path.exists():
        path.unlink()


def _cleanup_test_db() -> None:
    for path in (TEST_DB, Path(f"{TEST_DB}-wal"), Path(f"{TEST_DB}-shm")):
        try:
            path.unlink()
        except FileNotFoundError:
            pass


atexit.register(_cleanup_test_db)

from integrations.pms.mock_adapter import MockPMSAdapter  # noqa: E402
from main import app  # noqa: E402
import main  # noqa: E402


@pytest.fixture
def client():
    # Each integration test gets a fresh mock PMS state. The application services
    # are intentionally shared, so only the mutable adapter needs to be reset.
    main._pms.adapter = MockPMSAdapter()
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
