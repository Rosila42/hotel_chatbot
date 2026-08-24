from __future__ import annotations


def test_housekeeping_cannot_run_automation(client, housekeeping_headers):
    response = client.post(
        "/chat",
        json={"message": "run automation MORNING_ARRIVAL_CHECK"},
        headers=housekeeping_headers,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is False
    assert body["command"] == "RUN_AUTOMATION"
    assert "not authorized" in body["message"].lower()


def test_reception_cannot_disable_automation(client, reception_headers):
    response = client.post(
        "/chat",
        json={"message": "disable automation MORNING_ARRIVAL_CHECK"},
        headers=reception_headers,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is False
    assert body["command"] == "DISABLE_AUTOMATION"
    assert "not authorized" in body["message"].lower()


def test_manager_can_request_automation_run_and_confirm(client, manager_headers):
    request_response = client.post(
        "/chat",
        json={"message": "run automation MORNING_ARRIVAL_CHECK"},
        headers=manager_headers,
    )

    assert request_response.status_code == 200, request_response.text
    request_body = request_response.json()
    assert request_body["success"] is False
    assert request_body["command"] == "RUN_AUTOMATION"
    assert "confirm" in request_body["message"].lower()

    confirm_response = client.post(
        "/chat",
        json={"message": "confirm", "session_id": request_body["session_id"]},
        headers=manager_headers,
    )

    assert confirm_response.status_code == 200, confirm_response.text
    confirm_body = confirm_response.json()
    assert confirm_body["success"] is True, confirm_body
    assert confirm_body["command"] == "RUN_AUTOMATION"
