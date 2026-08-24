import pytest
from fastapi.testclient import TestClient

# TODO: Adjust this import to match your actual app location
from main import app

client = TestClient(app)

AUTH_TOKEN = "demo-manager-token"
HEADERS = {"Authorization": f"Bearer {AUTH_TOKEN}"}

def test_management_requests_operational_summary():
    """1. Requests operational summary"""
    response = client.post(
        "/chat", 
        json={"message": "operational summary"}, 
        headers=HEADERS
    )
    assert response.status_code == 200, response.text
    assert response.json().get("command") == "GET_OPERATIONAL_SUMMARY"

def test_management_lists_automations():
    """2. Lists automations"""
    response = client.post(
        "/chat", 
        json={"message": "list automations"}, 
        headers=HEADERS
    )
    assert response.status_code == 200, response.text
    assert response.json().get("command") == "LIST_AUTOMATIONS"

def test_management_runs_morning_arrival_check_with_confirmation():
    """3. Runs MORNING_ARRIVAL_CHECK (with confirmation)"""
    response1 = client.post(
        "/chat", 
        json={"message": "run automation MORNING_ARRIVAL_CHECK"}, 
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
        # Verify the automation actually executed after confirmation
        assert response2.json().get("command") == "RUN_AUTOMATION"

def test_management_reviews_automation_history():
    """4. Reviews automation history"""
    response = client.post(
        "/chat", 
        json={"message": "show automation history"}, 
        headers=HEADERS
    )
    assert response.status_code == 200, response.text
    assert response.json().get("command") == "GET_AUTOMATION_HISTORY"