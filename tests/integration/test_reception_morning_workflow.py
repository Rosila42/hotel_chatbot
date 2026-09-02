def test_morning_reception_full_flow(client, reception_headers):
    """Verify the Reception morning flow against the current /chat API contract."""
    requests = [
        ("today's arrivals", "GET_ARRIVALS"),
        ("which rooms aren't ready", "GET_ROOM_STATUS"),
        ("what time is checkout", "FAQ_SEARCH"),
        ("help", "HELP"),
        ("who is leaving today", "GET_DEPARTURES"),
    ]

    for message, expected_command in requests:
        response = client.post(
            "/chat",
            json={"message": message, "shift": "morning"},
            headers=reception_headers,
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["success"] is True, body
        assert body["command"] == expected_command, body


def test_reception_demo_reads_show_guest_and_room_details(client, reception_headers):
    arrivals = client.post(
        "/chat",
        json={"message": "Who is checking in today?", "shift": "morning"},
        headers=reception_headers,
    )

    assert arrivals.status_code == 200, arrivals.text
    arrivals_body = arrivals.json()
    assert arrivals_body["command"] == "GET_ARRIVALS"
    assert "John Martin" in arrivals_body["message"]
    assert "room 214" in arrivals_body["message"]
    assert "reservation r1" in arrivals_body["message"]
    assert "CONFIRMED" in arrivals_body["message"]

    readiness = client.post(
        "/chat",
        json={"message": "Which rooms are not ready for today's arrivals?", "shift": "morning"},
        headers=reception_headers,
    )

    assert readiness.status_code == 200, readiness.text
    readiness_body = readiness.json()
    assert readiness_body["command"] == "GET_ROOM_STATUS"
    assert "Room 214" in readiness_body["message"]
    assert "DIRTY" in readiness_body["message"]


def test_reception_can_report_ac_incident_then_confirm(client, reception_headers):
    request_response = client.post(
        "/chat",
        json={"message": "The air conditioning in room 214 isn't working", "shift": "morning"},
        headers=reception_headers,
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
        json={"message": "confirm", "session_id": request_body["session_id"], "shift": "morning"},
        headers=reception_headers,
    )

    assert confirm_response.status_code == 200, confirm_response.text
    confirm_body = confirm_response.json()
    assert confirm_body["success"] is True, confirm_body
    assert confirm_body["command"] == "CREATE_INCIDENT"
    assert "Incident created" in confirm_body["message"]
    assert "room 214" in confirm_body["message"]
    assert "MAINTENANCE" in confirm_body["message"]
    assert "isn't working" in confirm_body["message"]
