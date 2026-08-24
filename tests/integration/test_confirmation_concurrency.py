import pytest
from fastapi.testclient import TestClient
from concurrent.futures import ThreadPoolExecutor

# TODO: Adjust this import to match your actual app location
from main import app

# --- Fixtures ---
# If you already have these in a conftest.py, you can delete them from here
@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="module")
def reception_headers():
    # Use whatever token/headers your app expects for the "reception" role
    return {"Authorization": "Bearer test-reception-token"}

# --- Tests ---
def test_concurrent_confirmation_single_execution(client, reception_headers):
    # Issue the write
    client.post("/chat", json={"text": "report dirty room 214"}, headers=reception_headers)

    def confirm():
        return client.post("/chat", json={"text": "confirm"}, headers=reception_headers)

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(confirm) for _ in range(2)]
        results = [f.result() for f in futures]

    successes = [r for r in results if r.json().get("kind") == "SUCCESS"]
    assert len(successes) == 1, f"expected exactly one SUCCESS, got {len(successes)}"