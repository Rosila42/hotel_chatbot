from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EmptyParams(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SearchGuestParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)


class GetReservationParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reservation_id: str | None = Field(default=None, min_length=1)
    guest_name: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def require_lookup_criterion(self) -> "GetReservationParams":
        if not self.reservation_id and not self.guest_name:
            raise ValueError("at least one lookup criterion is required")
        return self


class DateParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: date | str | None = None


class RoomStatusParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    room_number: str | None = Field(default=None, min_length=1)
    filter: str | None = Field(default=None, min_length=1)


class RoomNumberParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    room_number: str = Field(min_length=1)


class IncidentFilterParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str | None = Field(default=None, min_length=1)
    room_number: str | None = Field(default=None, min_length=1)


class CreateIncidentParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    room_number: str | None = Field(default=None, min_length=1)
    incident_type: str = Field(min_length=1)
    description: str = Field(min_length=1, max_length=4000)


class ResolveIncidentParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    incident_id: str = Field(min_length=1)


class OperationalSummaryParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: date | str | None = None


class FAQSearchParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=4000)


class AutomationIdParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    automation_id: str = Field(min_length=1)
