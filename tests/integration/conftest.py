import pytest
from fastapi.testclient import TestClient
import os
os.environ["HOTEL_CHATBOT_TEST_DB"] = "/tmp/hotel-chatbot-test.db"
from main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def reception_headers():
    return {"Authorization": "Bearer demo-reception-token"}

@pytest.fixture
def housekeeping_headers():
    return {"Authorization": "Bearer demo-housekeeping-token"}

@pytest.fixture
def manager_headers():
    return {"Authorization": "Bearer demo-manager-token"}