from __future__ import annotations

from datetime import date
from typing import Callable, TypeVar

from integrations.pms.interface import PMSInterface
from models.pms import IncidentStatus, OperationalSummary, RoomStatus

T = TypeVar("T")


class PMSService:
    """Application-facing PMS boundary with bounded read retries and no unsafe write retries."""

    def __init__(self, adapter: PMSInterface, *, read_retries: int = 2) -> None:
        self.adapter = adapter
        self.read_retries = max(0, read_retries)

    def _read(self, operation: Callable[[], T]) -> T:
        attempts = self.read_retries + 1
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                return operation()
            except (TimeoutError, ConnectionError) as exc:
                last_error = exc
                if attempt == attempts - 1:
                    break
        assert last_error is not None
        raise last_error

    @staticmethod
    def _write(operation: Callable[[], T]) -> T:
        return operation()

    def search_guest(self, name: str):
        return self._read(lambda: self.adapter.search_guests(name))

    def get_reservation(self, reservation_id: str | None = None, guest_name: str | None = None):
        return self._read(lambda: self.adapter.get_reservation(reservation_id=reservation_id, guest_name=guest_name))

    def get_arrivals(self, on_date: date):
        return self._read(lambda: self.adapter.get_arrivals(on_date))

    def get_departures(self, on_date: date):
        return self._read(lambda: self.adapter.get_departures(on_date))

    def get_room_status(self, room_number: str | None = None, filter_name: str | None = None):
        if room_number:
            room = self._read(lambda: self.adapter.get_room(room_number))
            return [room] if room else []
        if not filter_name or filter_name == "all":
            return self._read(lambda: self.adapter.get_rooms())
        if filter_name == "not_ready_arrivals":
            rooms = []
            for reservation in self._read(lambda: self.adapter.get_arrivals(date.today())):
                room = self._read(lambda room_number=reservation.room_number: self.adapter.get_room(room_number))
                if room and room.status != RoomStatus.READY:
                    rooms.append(room)
            return rooms
        if filter_name == "not_ready":
            return self._read(lambda: [room for room in self.adapter.get_rooms() if room.status != RoomStatus.READY])
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
        return self._read(lambda: self.adapter.get_rooms(canonical[filter_name]))

    def mark_room_clean(self, room_number: str):
        return self._write(lambda: self.adapter.mark_room_clean(room_number))

    def get_incidents(self, status: str | None = None, room_number: str | None = None):
        incidents = self._read(lambda: self.adapter.get_incidents(status))
        return [i for i in incidents if not room_number or i.room_number == str(room_number)]

    def create_incident(self, room_number: str | None, incident_type: str, description: str):
        if not description.strip():
            raise ValueError("Incident description cannot be empty")
        if not incident_type.strip():
            raise ValueError("Incident type cannot be empty")
        if room_number and self._read(lambda: self.adapter.get_room(room_number)) is None:
            raise ValueError(f"Room {room_number} does not exist")
        return self._write(lambda: self.adapter.create_incident(room_number, incident_type, description))

    def resolve_incident(self, incident_id: str):
        return self._write(lambda: self.adapter.resolve_incident(incident_id))

    def get_operational_summary(self, on_date: date | None = None) -> OperationalSummary:
        target = on_date or date.today()
        arrivals = self.get_arrivals(target)
        departures = self.get_departures(target)
        rooms = self.get_room_status()
        open_incidents = self._read(lambda: self.adapter.get_incidents(IncidentStatus.OPEN.value))
        occupied = sum(room.status == RoomStatus.OCCUPIED for room in rooms)
        available = sum(room.status == RoomStatus.AVAILABLE for room in rooms)
        requiring_attention = sum(room.status in {RoomStatus.DIRTY, RoomStatus.CLEANING, RoomStatus.MAINTENANCE} for room in rooms)
        occupancy_rate = occupied / len(rooms) * 100 if rooms else 0.0
        return OperationalSummary(len(arrivals), len(departures), occupancy_rate, available, requiring_attention, len(open_incidents))
