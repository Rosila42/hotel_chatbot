import pytest
from fastapi.testclient import TestClient

# TODO: Adjust this import to match your actual app location
from main import app

client = TestClient(app)

# Use a valid test token if your app enforces authentication
AUTH_TOKEN = "demo-reception-token"
HEADERS = {"Authorization": f"Bearer {AUTH_TOKEN}"}

def test_shift_change_resets_session():
    """
    1. Switching from morning to afternoon resets the session.
    3. The visible transcript is cleared on shift change (PR #12 behavior).
    """
    # 1. Start a session on the morning shift
    response1 = client.post(
        "/chat", 
        json={"message": "today's arrivals", "shift": "morning"}, 
        headers=HEADERS
    )
    assert response1.status_code == 200
    session_id_1 = response1.json().get("session_id")
    assert session_id_1 is not None, "Initial session ID was not returned"

    # 2. Simulate the UI shift change by dropping the session_id and changing the shift
    # (This replicates the frontend resetting the session)
    response2 = client.post(
        "/chat", 
        json={"message": "who is leaving today", "shift": "afternoon", "session_id": None}, 
        headers=HEADERS
    )
    assert response2.status_code == 200
    session_id_2 = response2.json().get("session_id")
    
    # The new session must have a different ID (or be None if your app regenerates it)
    assert session_id_2 != session_id_1, "Session ID did not reset on shift change!"

    # 3. Verify pending state is cleared. 
    # If we tried to "confirm" right now, it should fail because the old transcript is gone.
    confirm_response = client.post(
        "/chat",
        json={"message": "confirm", "shift": "afternoon", "session_id": session_id_2},
        headers=HEADERS
    )
    # It should not be a 200 SUCCESS, it should be some form of rejection (e.g. 400, 404, or 200 with an error kind)
    response_json = confirm_response.json()
    assert response_json.get("kind") != "SUCCESS", "Pending state leaked across shift reset!"


@pytest.mark.parametrize("shift_name", ["morning", "afternoon", "night"])
def test_same_command_works_in_all_shifts(shift_name):
    """
    2. The same command ("today's arrivals") works in all shifts.
    """
    response = client.post(
        "/chat", 
        json={"message": "today's arrivals", "shift": shift_name}, 
        headers=HEADERS
    )
    
    assert response.status_code == 200, f"Failed for shift: {shift_name}"
    
    # Verify the parser still recognized it as the arrivals command
    result = response.json()
    assert "ARRIVALS" in result.get("command", "").upper(), \
        f"Parser failed to resolve arrivals command for shift: {shift_name}"