import pytest
from fastapi.testclient import TestClient

# TODO: Adjust these imports to match your actual project structure
from main import app  # Or wherever your FastAPI 'app' instance lives
# from core.database import SessionLocal, AuditLog  # Uncomment and adjust for your DB models

client = TestClient(app)

# Use a valid test token if your app enforces authentication
AUTH_TOKEN = "test-token"
HEADERS = {"Authorization": f"Bearer {AUTH_TOKEN}"}

@pytest.mark.parametrize(
    "text, command_name",
    [
        ("today's arrivals", "arrivals"),
        ("who is leaving today", "departures"),
        ("status of room 214", "room_status"),
        ("find guest Smith", "guest_search"),
        ("help", "help"),
        ("operational summary", "operational_summary"),
        ("what time is checkout", "faq"),
    ]
)
def test_chat_read_paths(text, command_name):
    """
    Tests the read-path of the /chat endpoint.
    Asserts 200 OK, correct response shape, and verifies an audit row is written.
    """
    # 1. POST to /chat with the appropriate bearer token
    response = client.post("/chat", json={"text": text}, headers=HEADERS)
    
    # 2. Assert HTTP 200
    assert response.status_code == 200, f"Failed for input '{text}'. Response: {response.text}"
    
    # 3. Assert the response shape matches the command's expected CommandResult
    # Assuming CommandResult returns a JSON dict with 'command' and 'data' or 'status'
    result = response.json()
    assert result is not None, "Response body was empty"
    assert "command" in result, f"Missing 'command' field in response for {command_name}"
    assert result["command"] == command_name, f"Expected command '{command_name}', got {result.get('command')}"
    
    # 4. Query the DB afterward to confirm an audit row was written
    # NOTE: You will need to uncomment and adjust this section to match your actual 
    # database session and AuditLog model.
    # 
    # db = SessionLocal()
    # try:
    #     audit_record = db.query(AuditLog).filter(
    #         AuditLog.input_text == text
    #     ).order_by(AuditLog.id.desc()).first()
    #     
    #     assert audit_record is not None, f"No audit log was written for input: {text}"
    #     assert audit_record.command == command_name
    # finally:
    #     db.close()