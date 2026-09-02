from __future__ import annotations


def test_write_command_requires_confirmation_then_succeeds(client, housekeeping_headers):
    request_response = client.post(
        "/chat",
        json={"message": "report dirty room 214"},
        headers=housekeeping_headers,
    )

    assert request_response.status_code == 200, request_response.text
    request_body = request_response.json()
    assert request_body["success"] is False
    assert request_body["command"] == "CREATE_INCIDENT"
    assert "confirm" in request_body["message"].lower()

    confirm_response = client.post(
        "/chat",
        json={"message": "confirm", "session_id": request_body["session_id"]},
        headers=housekeeping_headers,
    )

    assert confirm_response.status_code == 200, confirm_response.text
    confirm_body = confirm_response.json()
    assert confirm_body["success"] is True, confirm_body
    assert confirm_body["command"] == "CREATE_INCIDENT"
    assert confirm_body["data"] is not None


def test_natural_ac_incident_creation_requires_confirmation_then_succeeds(client, housekeeping_headers):
    request_response = client.post(
        "/chat",
        json={"message": "The air conditioning in room 214 isn't working"},
        headers=housekeeping_headers,
    )

    assert request_response.status_code == 200, request_response.text
    request_body = request_response.json()
    assert request_body["success"] is False
    assert request_body["command"] == "CREATE_INCIDENT"
    assert request_body["parameters"]["room_number"] == "214"
    assert request_body["parameters"]["incident_type"] == "MAINTENANCE"
    assert "confirm" in request_body["message"].lower()

    confirm_response = client.post(
        "/chat",
        json={"message": "confirm", "session_id": request_body["session_id"]},
        headers=housekeeping_headers,
    )

    assert confirm_response.status_code == 200, confirm_response.text
    confirm_body = confirm_response.json()
    assert confirm_body["success"] is True, confirm_body
    assert confirm_body["command"] == "CREATE_INCIDENT"
    assert confirm_body["data"] is not None
    assert "Incident created" in confirm_body["message"]
    assert "room 214" in confirm_body["message"]
    assert "MAINTENANCE" in confirm_body["message"]
    assert "isn't working" in confirm_body["message"]


def test_write_command_can_be_cancelled(client, housekeeping_headers):
    request_response = client.post(
        "/chat",
        json={"message": "report dirty room 214"},
        headers=housekeeping_headers,
    )

    assert request_response.status_code == 200, request_response.text
    session_id = request_response.json()["session_id"]

    cancel_response = client.post(
        "/chat",
        json={"message": "cancel", "session_id": session_id},
        headers=housekeeping_headers,
    )

    assert cancel_response.status_code == 200, cancel_response.text
    body = cancel_response.json()
    assert body["success"] is True
    assert body["command"] is None
    assert "cancelled" in body["message"].lower()
