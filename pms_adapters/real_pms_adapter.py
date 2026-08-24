from __future__ import annotations

import logging
import os
import uuid
from datetime import date
from typing import Optional

import httpx

from integrations.pms.interface import PMSInterface
from models.pms import Guest, Incident, Reservation, Room, RoomStatus

logger = logging.getLogger(__name__)


class RealPMSAdapter(PMSInterface):
    """REST-based PMS adapter kept behind the PMSInterface boundary."""

    def __init__(
        self,
        base_url: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        client: httpx.Client | None = None,
    ):
        self.base_url = (
            base_url
            if base_url is not None
            else os.getenv("HOTEL_CHATBOT_PMS_BASE_URL", "https://api.pms.com/v1")
        )
        self.client_id = client_id or os.getenv("PMS_CLIENT_ID", "test_id")
        self.client_secret = client_secret or os.getenv("PMS_CLIENT_SECRET", "test_secret")
        self._token: Optional[str] = None
        self._client = client or httpx.Client(timeout=httpx.Timeout(5.0, read=3.0))

    def _get_auth_token(self) -> str:
        """Fetch and cache an access token placeholder until PMS OAuth is integrated."""
        if self._token:
            return self._token
        logger.info("Fetching PMS OAuth2 token placeholder...")
        self._token = "dummy-access-token-xyz"
        return self._token

    def _request(self, method: str, endpoint: str, is_read: bool = True, **kwargs) -> dict:
        """Execute a PMS request with auth and bounded retry policy."""
        headers = dict(kwargs.pop("headers", {}))
        headers["Authorization"] = f"Bearer {self._get_auth_token()}"
        headers["X-Operation-Id"] = str(uuid.uuid4())

        attempts = 3 if is_read else 1
        last_exc: Exception | None = None

        for attempt in range(attempts):
            try:
                response = self._client.request(
                    method,
                    f"{self.base_url}{endpoint}",
                    headers=headers,
                    **kwargs,
                )
                response.raise_for_status()
                return response.json()
            except (httpx.ConnectTimeout, httpx.ReadTimeout) as exc:
                last_exc = exc
            except httpx.HTTPStatusError:
                # Preserve HTTP errors so callers can distinguish 404/not-found
                # from transport failures and map them appropriately.
                raise

            logger.warning(
                "PMS request timeout (attempt %s/%s)",
                attempt + 1,
                attempts,
            )
            if not is_read or attempt == attempts - 1:
                break

        raise ConnectionError(
            f"Failed to communicate with PMS after {attempts} attempts."
        ) from last_exc

    def search_guests(self, name: str) -> list[Guest]:
        data = self._request("GET", "/guests", params={"name": name})
        return [Guest(**guest) for guest in data.get("guests", [])]

    def get_reservation(self, reservation_id: str | None = None, guest_name: str | None = None) -> list[Reservation]:
        params = {}
        if reservation_id:
            params["reservation_id"] = reservation_id
        if guest_name:
            params["guest_name"] = guest_name
        data = self._request("GET", "/reservations", params=params)
        return [Reservation(**reservation) for reservation in data.get("reservations", [])]

    def get_arrivals(self, on_date: date) -> list[Reservation]:
        data = self._request(
            "GET",
            "/reservations",
            params={"arrival": on_date.isoformat(), "status": "reserved"},
        )
        return [Reservation(**reservation) for reservation in data.get("reservations", [])]

    def get_departures(self, on_date: date) -> list[Reservation]:
        data = self._request(
            "GET",
            "/reservations",
            params={"departure": on_date.isoformat(), "status": "in_house"},
        )
        return [Reservation(**reservation) for reservation in data.get("reservations", [])]

    def get_room(self, room_number: str) -> Room | None:
        try:
            data = self._request("GET", f"/rooms/{room_number}")
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            raise
        return Room(**data)

    def get_rooms(self, status: RoomStatus | None = None) -> list[Room]:
        params = {"status": status.value if status else None}
        data = self._request("GET", "/rooms", params=params)
        return [Room(**room) for room in data.get("rooms", [])]

    def mark_room_clean(self, room_number: str) -> Room:
        data = self._request(
            "PUT",
            f"/rooms/{room_number}/status",
            json={"status": "CLEAN"},
            is_read=False,
        )
        return Room(**data)

    def get_incidents(self, status: str | None = None) -> list[Incident]:
        data = self._request("GET", "/incidents", params={"status": status})
        return [Incident(**incident) for incident in data.get("incidents", [])]

    def create_incident(self, room_number: str | None, incident_type: str, description: str) -> Incident:
        payload = {"type": incident_type, "description": description}
        if room_number:
            payload["room_number"] = room_number
        data = self._request("POST", "/incidents", json=payload, is_read=False)
        return Incident(**data)

    def resolve_incident(self, incident_id: str) -> Incident:
        data = self._request("PUT", f"/incidents/{incident_id}/resolve", is_read=False)
        return Incident(**data)
