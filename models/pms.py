from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum


class RoomStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    DIRTY = "DIRTY"
    CLEANING = "CLEANING"
    READY = "READY"
    MAINTENANCE = "MAINTENANCE"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"


class IncidentStatus(str, Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


@dataclass(frozen=True)
class Guest:
    guest_id: str
    name: str


@dataclass(frozen=True)
class Reservation:
    reservation_id: str
    guest_id: str
    guest_name: str
    room_number: str
    arrival: date
    departure: date
    status: str


@dataclass(frozen=True)
class Room:
    room_number: str
    status: RoomStatus
    room_type: str


@dataclass(frozen=True)
class Incident:
    incident_id: str
    room_number: str | None
    incident_type: str
    description: str
    status: IncidentStatus
    created_at: datetime


@dataclass(frozen=True)
class OperationalSummary:
    arrivals: int
    departures: int
    occupancy_rate: float
    available_rooms: int
    rooms_requiring_attention: int
    open_incidents: int
