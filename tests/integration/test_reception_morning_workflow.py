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
