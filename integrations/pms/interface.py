from __future__ import annotations

from datetime import date
from typing import Protocol

from models.pms import Guest, Incident, Reservation, Room, RoomStatus


class PMSInterface(Protocol):
    """
    Formal contract for all Property Management System (PMS) adapters.
    Any concrete adapter (e.g., MockPMSAdapter, OracleOPERAAdapter) MUST adhere to this contract.
    """

    def search_guests(self, name: str) -> list[Guest]:
        """
        Searches for guests by name.
        Input/Output: Takes a name string, returns a list of Guest objects (empty if none).
        Failure Semantics: Raises ConnectionError if PMS is unreachable.
        Idempotency: IDEMPOTENT (Read-only).
        """
        ...

    def get_reservation(self, reservation_id: str | None = None, guest_name: str | None = None) -> list[Reservation]:
        """
        Retrieves reservations by ID or guest name.
        Input/Output: Takes optional reservation_id or guest_name, returns a list of Reservations.
        Failure Semantics: Raises ConnectionError if PMS is unreachable. Raises ValueError if formatting is invalid.
        Idempotency: IDEMPOTENT (Read-only).
        """
        ...

    def get_arrivals(self, on_date: date) -> list[Reservation]:
        """
        Retrieves arrivals for a specific date.
        Input/Output: Takes a date object, returns a list of Reservations.
        Failure Semantics: Raises ConnectionError if PMS is unreachable.
        Idempotency: IDEMPOTENT (Read-only).
        """
        ...

    def get_departures(self, on_date: date) -> list[Reservation]:
        """
        Retrieves departures for a specific date.
        Input/Output: Takes a date object, returns a list of Reservations.
        Failure Semantics: Raises ConnectionError if PMS is unreachable.
        Idempotency: IDEMPOTENT (Read-only).
        """
        ...

    def get_room(self, room_number: str) -> Room | None:
        """
        Retrieves a single room by room number.
        Input/Output: Takes a room number string, returns a Room object or None if not found.
        Failure Semantics: Raises ConnectionError if PMS is unreachable.
        Idempotency: IDEMPOTENT (Read-only).
        """
        ...

    def get_rooms(self, status: RoomStatus | None = None) -> list[Room]:
        """
        Retrieves all rooms, optionally filtered by status.
        Input/Output: Takes an optional RoomStatus enum, returns a list of Rooms.
        Failure Semantics: Raises ConnectionError if PMS is unreachable.
        Idempotency: IDEMPOTENT (Read-only).
        """
        ...

    def mark_room_clean(self, room_number: str) -> Room:
        """
        Marks a specific room as clean/ready.
        Input/Output: Takes a room number string, returns the updated Room object.
        Failure Semantics: Raises ConnectionError if PMS is unreachable. Raises ValueError if room does not exist. Raises PermissionError if API token lacks write access.
        Idempotency: IDEMPOTENT (Calling on an already clean room returns success without side effects).
        """
        ...

    def get_incidents(self, status: str | None = None) -> list[Incident]:
        """
        Retrieves incidents, optionally filtered by status.
        Input/Output: Takes an optional status string, returns a list of Incidents.
        Failure Semantics: Raises ConnectionError if PMS is unreachable.
        Idempotency: IDEMPOTENT (Read-only).
        """
        ...

    def create_incident(self, room_number: str | None, incident_type: str, description: str) -> Incident:
        """
        Creates a new incident in the PMS.
        Input/Output: Takes room number, type, and description. Returns the created Incident object.
        Failure Semantics: Raises ConnectionError if PMS is unreachable. Raises ValueError if room_number is invalid. Raises PermissionError if lacks write access.
        Idempotency: NON-IDEMPOTENT (Calling twice creates two separate incidents).
        """
        ...

    def resolve_incident(self, incident_id: str) -> Incident:
        """
        Marks an existing incident as resolved.
        Input/Output: Takes an incident_id string, returns the updated Incident object.
        Failure Semantics: Raises ConnectionError if PMS is unreachable. Raises ValueError if incident_id does not exist. Raises PermissionError if lacks write access.
        Idempotency: IDEMPOTENT (Calling on an already resolved incident returns success without side effects).
        """
        ...