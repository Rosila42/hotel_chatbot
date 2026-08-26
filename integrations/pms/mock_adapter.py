from __future__ import annotations

from collections import OrderedDict
from datetime import date, datetime, timedelta

from models.pms import Guest, Incident, IncidentStatus, Reservation, Room, RoomStatus


class MockPMSAdapter:
    """In-memory PMS adapter used for local development and portfolio demos."""

    def __init__(self) -> None:
        today = date.today()
        self.guests = {"g1": Guest("g1", "John Martin"), "g2": Guest("g2", "Anna Silva")}
        self.rooms = OrderedDict((
            ("101", Room("101", RoomStatus.READY, "double")),
            ("102", Room("102", RoomStatus.DIRTY, "double")),
            ("201", Room("201", RoomStatus.OCCUPIED, "suite")),
            ("214", Room("214", RoomStatus.DIRTY, "double")),
            ("301", Room("301", RoomStatus.AVAILABLE, "single")),
        ))
        self.reservations = [
            Reservation("r1", "g1", "John Martin", "214", today, today + timedelta(days=3), "CONFIRMED"),
            Reservation("r2", "g2", "Anna Silva", "101", today + timedelta(days=1), today + timedelta(days=4), "CONFIRMED"),
        ]
        # Keep room 214 free of a pre-existing maintenance incident so the demo
        # can create the AC incident and visibly show the resulting state change.
        self.incidents: dict[str, Incident] = {
            "i1": Incident(
                "i1",
                "102",
                "HOUSEKEEPING",
                "Room requires additional cleaning",
                IncidentStatus.OPEN,
                datetime.now(),
            )
        }

    def search_guests(self, name: str) -> list[Guest]:
        needle = name.strip().lower()
        return [guest for guest in self.guests.values() if needle in guest.name.lower()]

    def get_reservation(self, reservation_id: str | None = None, guest_name: str | None = None) -> list[Reservation]:
        results = self.reservations
        if reservation_id:
            results = [r for r in results if r.reservation_id == reservation_id]
        if guest_name:
            needle = guest_name.strip().lower()
            results = [r for r in results if needle in r.guest_name.lower()]
        return results

    def get_arrivals(self, on_date: date) -> list[Reservation]:
        return [r for r in self.reservations if r.arrival == on_date]

    def get_departures(self, on_date: date) -> list[Reservation]:
        return [r for r in self.reservations if r.departure == on_date]

    def get_room(self, room_number: str) -> Room | None:
        return self.rooms.get(str(room_number))

    def get_rooms(self, status: RoomStatus | None = None) -> list[Room]:
        rooms = list(self.rooms.values())
        return [room for room in rooms if status is None or room.status == status]

    def mark_room_clean(self, room_number: str) -> Room:
        room = self.get_room(room_number)
        if room is None:
            raise ValueError(f"Room {room_number} does not exist")
        if room.status not in {RoomStatus.DIRTY, RoomStatus.CLEANING}:
            raise ValueError(f"Room {room_number} cannot be marked clean from {room.status.value}")
        updated = Room(room.room_number, RoomStatus.READY, room.room_type)
        self.rooms[room.room_number] = updated
        return updated

    def get_incidents(self, status: str | None = None) -> list[Incident]:
        incidents = list(self.incidents.values())
        if status:
            incidents = [incident for incident in incidents if incident.status.value == status.upper()]
        return incidents

    def create_incident(self, room_number: str | None, incident_type: str, description: str) -> Incident:
        incident_id = f"i{len(self.incidents) + 1}"
        incident = Incident(
            incident_id,
            str(room_number) if room_number else None,
            incident_type.upper(),
            description.strip(),
            IncidentStatus.OPEN,
            datetime.now(),
        )
        self.incidents[incident_id] = incident
        return incident

    def resolve_incident(self, incident_id: str) -> Incident:
        incident = self.incidents.get(incident_id)
        if incident is None:
            raise ValueError(f"Incident {incident_id} does not exist")
        if incident.status == IncidentStatus.RESOLVED:
            return incident
        resolved = Incident(
            incident.incident_id,
            incident.room_number,
            incident.incident_type,
            incident.description,
            IncidentStatus.RESOLVED,
            incident.created_at,
        )
        self.incidents[incident_id] = resolved
        return resolved
