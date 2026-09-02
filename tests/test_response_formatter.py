from datetime import date, datetime

from models.pms import Incident, IncidentStatus, OperationalSummary, Reservation, Room, RoomStatus
from services.response_formatter import ResponseFormatter


def test_formatter_includes_arrival_guest_and_room_details():
    reservation = Reservation(
        "r1",
        "g1",
        "John Martin",
        "214",
        date(2026, 9, 2),
        date(2026, 9, 5),
        "CONFIRMED",
    )

    message = ResponseFormatter.format("GET_ARRIVALS", [reservation])

    assert "John Martin" in message
    assert "room 214" in message
    assert "r1" in message
    assert "CONFIRMED" in message


def test_formatter_includes_room_numbers_and_statuses():
    rooms = [
        Room("102", RoomStatus.DIRTY, "double"),
        Room("214", RoomStatus.DIRTY, "double"),
    ]

    message = ResponseFormatter.format("GET_ROOM_STATUS", rooms)

    assert "Room 102" in message
    assert "Room 214" in message
    assert "DIRTY" in message


def test_formatter_includes_incident_details():
    incident = Incident(
        "i2",
        "214",
        "MAINTENANCE",
        "The air conditioning in room 214 isn't working",
        IncidentStatus.OPEN,
        datetime(2026, 9, 2, 19, 0),
    )

    message = ResponseFormatter.format("CREATE_INCIDENT", incident)

    assert "i2" in message
    assert "room 214" in message
    assert "MAINTENANCE" in message
    assert "isn't working" in message
    assert "OPEN" in message


def test_formatter_includes_operational_summary_metrics():
    summary = OperationalSummary(2, 1, 40.0, 1, 2, 3)

    message = ResponseFormatter.format("GET_OPERATIONAL_SUMMARY", summary)

    assert "Arrivals: 2" in message
    assert "Departures: 1" in message
    assert "Occupancy: 40.0%" in message
    assert "Available rooms: 1" in message
    assert "Rooms requiring attention: 2" in message
    assert "Open incidents: 3" in message


def test_formatter_includes_empty_results_without_hiding_the_state():
    assert ResponseFormatter.format("GET_ARRIVALS", []) == "No arrivals found."
    assert ResponseFormatter.format("GET_ROOM_STATUS", []) == "No matching rooms found."
    assert ResponseFormatter.format("GET_INCIDENTS", []) == "No matching incidents found."
