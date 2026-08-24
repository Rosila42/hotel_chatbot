import pytest
from fastapi.testclient import TestClient

# TODO: Adjust this import to match your actual app location
from main import app

client = TestClient(app)

AUTH_TOKEN = "demo-housekeeping-token"
HEADERS = {"Authorization": f"Bearer {AUTH_TOKEN}"}

def test_housekeeping_list_dirty_rooms():
    """1. List rooms that need cleaning"""
    response = client.post(
        "/chat", 
        json={"message": "which rooms are not ready?"}, 
        headers=HEADERS
    )
    assert response.status_code == 200, response.text
    assert "ROOM" in response.json().get("command", "").upper()

def test_housekeeping_mark_room_clean_with_confirmation():
    """2. Mark a room clean (with confirmation)"""
    response = client.post(
        "/chat", 
        json={"message": "mark room 214 clean"}, 
        headers=HEADERS
    )
    assert response.status_code == 200, response.text
    
    result = response.json()
    # Your app returns the command directly. If it requires confirmation, 
    # we simulate the confirm step.
    if "confirm" in result.get("message", "").lower():
        session_id = result.get("session_id")
        response2 = client.post(
            "/chat", 
            json={"message": "confirm", "session_id": session_id}, 
            headers=HEADERS
        )
        assert response2.status_code == 200, response2.text

def test_housekeeping_view_open_incidents():
    """3. View open incidents on rooms"""
    response = client.post(
        "/chat", 
        json={"message": "show open incidents"}, 
        headers=HEADERS
    )
    assert response.status_code == 200, response.text
    assert "INCIDENT" in response.json().get("command", "").upper()

def test_housekeeping_resolve_incident_with_confirmation():
    """4. Resolve an incident (with confirmation)"""
    response1 = client.post(
        "/chat", 
        json={"message": "resolve incident 42"}, 
        headers=HEADERS
    )
    assert response1.status_code == 200, response1.text
    
    result1 = response1.json()
    # If the app asks for confirmation, send it
    if "confirm" in result1.get("message", "").lower():
        session_id = result1.get("session_id")
        response2 = client.post(
            "/chat", 
            json={"message": "confirm", "session_id": session_id}, 
            headers=HEADERS
        )
        assert response2.status_code == 200, response2.text

def test_housekeeping_denied_reception_commands():
    """5. Denied reception-only commands per the registry's permission rules"""
    response = client.post(
        "/chat", 
        json={"message": "today's arrivals"}, 
        headers=HEADERS
    )
    
    assert response.status_code in [200, 403], response.text
    
    result = response.json()
    # Your backend parses the command but denies the data and returns an error message
    assert result.get("data") is None, "Housekeeping token received data for a denied command!"
    assert "not authorized" in result.get("message", "").lower(), "Missing authorization denial message!"