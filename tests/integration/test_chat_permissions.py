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


def test_manager_is_authorized_to_run_automation(client, manager_headers):
    response = client.post(
        "/chat",
        json={"message": "run automation MORNING_ARRIVAL_CHECK"},
        headers=manager_headers,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    # Authorization succeeds before confirmation and before automation state is checked.
    assert body["command"] == "RUN_AUTOMATION"
    assert "confirm" in body["message"].lower()
    assert "not authorized" not in body["message"].lower()
