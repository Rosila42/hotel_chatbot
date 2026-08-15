from __future__ import annotations

from datetime import date

from hotel_chatbot_v2.integrations.pms.interface import PMSInterface
from hotel_chatbot_v2.models.pms import IncidentStatus, OperationalSummary, RoomStatus


class PMSService:
    """Application-level PMS operations and cross-resource composition."""

    def __init__(self, adapter: PMSInterface) -> None:
        self.adapter = adapter

    def search_guest(self, name: str):
        return self.adapter.search_guests(name)

    def get_reservation(self, reservation_id: str | None = None, guest_name: str | None = None):
        return self.adapter.get_reservation(reservation_id=reservation_id, guest_name=guest_name)

    def get_arrivals(self, on_date: date):
        return self.adapter.get_arrivals(on_date)

    def get_departures(self, on_date: date):
        return self.adapter.get_departures(on_date)

    def get_room_status(self, room_number: str | None = None, filter_name: str | None = None):
        if room_number:
            room = self.adapter.get_room(room_number)
            return [room] if room else []

        if not filter_name or filter_name == "all":
            return self.adapter.get_rooms()

        if filter_name == "not_ready_arrivals":
            arrivals = self.adapter.get_arrivals(date.today())
            rooms = []
            for reservation in arrivals:
                room = self.adapter.get_room(reservation.room_number)
                if room and room.status != RoomStatus.READY:
                    rooms.append(room)
            return rooms

        canonical = {
            "available": RoomStatus.AVAILABLE,
            "occupied": RoomStatus.OCCUPIED,
            "dirty": RoomStatus.DIRTY,
            "cleaning": RoomStatus.CLEANING,
            "ready": RoomStatus.READY,
            "maintenance": RoomStatus.MAINTENANCE,
            "out_of_service": RoomStatus.OUT_OF_SERVICE,
        }
        if filter_name not in canonical:
            raise ValueError(f"Unsupported room filter: {filter_name}")
        return self.adapter.get_rooms(canonical[filter_name])

    def mark_room_clean(self, room_number: str):
        return self.adapter.mark_room_clean(room_number)

    def get_incidents(self, status: str | None = None, room_number: str | None = None):
        incidents = self.adapter.get_incidents(status)
        if room_number:
            incidents = [incident for incident in incidents if incident.room_number == str(room_number)]
        return incidents

    def create_incident(self, room_number: str | None, incident_type: str, description: str):
        if not description.strip():
            raise ValueError("Incident description cannot be empty")
        if not incident_type.strip():
            raise ValueError("Incident type cannot be empty")
        if room_number and self.adapter.get_room(room_number) is None:
            raise ValueError(f"Room {room_number} does not exist")
        return self.adapter.create_incident(room_number, incident_type, description)

    def resolve_incident(self, incident_id: str):
        return self.adapter.resolve_incident(incident_id)

    def get_operational_summary(self, on_date: date | None = None) -> OperationalSummary:
        target = on_date or date.today()
        arrivals = self.adapter.get_arrivals(target)
        departures = self.adapter.get_departures(target)
        rooms = self.adapter.get_rooms()
        open_incidents = self.adapter.get_incidents(IncidentStatus.OPEN.value)
        occupied = sum(room.status == RoomStatus.OCCUPIED for room in rooms)
        available = sum(room.status == RoomStatus.AVAILABLE for room in rooms)
        requiring_attention = sum(
            room.status in {RoomStatus.DIRTY, RoomStatus.CLEANING, RoomStatus.MAINTENANCE}
            for room in rooms
        )
        occupancy_rate = (occupied / len(rooms) * 100) if rooms else 0.0
        return OperationalSummary(
            arrivals=len(arrivals),
            departures=len(departures),
            occupancy_rate=occupancy_rate,
            available_rooms=available,
            rooms_requiring_attention=requiring_attention,
            open_incidents=len(open_incidents),
        )
