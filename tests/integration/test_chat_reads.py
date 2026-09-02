from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    ("message", "expected_command", "header_fixture"),
    [
        ("today's arrivals", "GET_ARRIVALS", "reception_headers"),
        ("who is leaving today", "GET_DEPARTURES", "reception_headers"),
        ("status of room 214", "GET_ROOM_STATUS", "reception_headers"),
        ("find guest Smith", "SEARCH_GUEST", "reception_headers"),
        ("help", "HELP", "reception_headers"),
        ("operational summary", "GET_OPERATIONAL_SUMMARY", "manager_headers"),
        ("what time is checkout", "FAQ_SEARCH", "reception_headers"),
    ],
)
def test_chat_read_only_commands(
    client,
    request,
    message: str,
    expected_command: str,
    header_fixture: str,
):
    headers = request.getfixturevalue(header_fixture)
    response = client.post("/chat", json={"message": message}, headers=headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True, body
    assert body["command"] == expected_command, body


@pytest.mark.parametrize(
    "message, expected_command",
    [
        ("today's arrivals", "GET_ARRIVALS"),
        ("who is leaving today", "GET_DEPARTURES"),
        ("status of room 214", "GET_ROOM_STATUS"),
        ("find guest John", "SEARCH_GUEST"),
        ("help", "HELP"),
        ("what time is checkout", "FAQ_SEARCH"),
    ],
)
def test_reception_can_execute_supported_reads(
    client,
    reception_headers,
    message: str,
    expected_command: str,
):
    response = client.post("/chat", json={"message": message}, headers=reception_headers)

    assert response.status_code == 200, response.text
    assert response.json()["success"] is True
    assert response.json()["command"] == expected_command


def test_manager_can_execute_operational_summary(client, manager_headers):
    response = client.post("/chat", json={"message": "operational summary"}, headers=manager_headers)

    assert response.status_code == 200, response.text
    assert response.json()["success"] is True
    assert response.json()["command"] == "GET_OPERATIONAL_SUMMARY"


def test_arrivals_response_shows_guest_and_room_details(client, reception_headers):
    response = client.post("/chat", json={"message": "Who is checking in today?"}, headers=reception_headers)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["command"] == "GET_ARRIVALS"
    assert "John Martin" in body["message"]
    assert "room 214" in body["message"]
    assert "r1" in body["message"]


def test_not_ready_response_shows_room_numbers(client, reception_headers):
    response = client.post(
        "/chat",
        json={"message": "Which rooms are not ready for today's arrivals?"},
        headers=reception_headers,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["command"] == "GET_ROOM_STATUS"
    assert "Room 214" in body["message"]
    assert "DIRTY" in body["message"]
