import os
import uuid
import logging
from datetime import date
from typing import Optional

import httpx

# Adjust these imports to match your actual project structure
from integrations.pms.interface import PMSInterface
from models.pms import Guest, Incident, Reservation, Room, RoomStatus

logger = logging.getLogger(__name__)

class RealPMSAdapter(PMSInterface):
    """
    Production PMS Adapter implementing the PMSInterface.
    Communicates with a REST-based Cloud PMS (e.g., Oracle OPERA Cloud).
    """

    def __init__(self, base_url: str = None, client_id: str = None, client_secret: str = None, client: httpx.Client = None):
        #self.base_url = base_url or os.getenv("PMS_API_BASE_URL", "https://api.pms.com/v1")
        # This allows us to pass an empty string "" for testing
        self.base_url = base_url if base_url is not None else os.getenv("PMS_API_BASE_URL", "https://api.pms.com/v1")
        self.client_id = client_id or os.getenv("PMS_CLIENT_ID", "test_id")
        self.client_secret = client_secret or os.getenv("PMS_CLIENT_SECRET", "test_secret")
        self._token: Optional[str] = None
        
        # Use the injected client for testing, or create a real one for production
        self._client = client or httpx.Client(timeout=httpx.Timeout(5.0, read=3.0))
    '''        
    def __init__(self, base_url: str = None, client_id: str = None, client_secret: str = None):
        self.base_url = base_url or os.getenv("PMS_API_BASE_URL", "https://api.pms.com/v1")
        self.client_id = client_id or os.getenv("PMS_CLIENT_ID", "test_id")
        self.client_secret = client_secret or os.getenv("PMS_CLIENT_SECRET", "test_secret")
        self._token: Optional[str] = None
        
        # Timeouts from our design doc: 3s read, 5s write
        self._client = httpx.Client(timeout=httpx.Timeout(5.0, read=3.0))
    '''

    def _get_auth_token(self) -> str:
        """Fetches and caches the OAuth2 bearer token."""
        if self._token:
            return self._token
            
        # In a real scenario, this would POST to the PMS token endpoint
        logger.info("Fetching new PMS OAuth2 token...")
        self._token = "dummy-access-token-xyz"
        return self._token

    def _request(self, method: str, endpoint: str, is_read: bool = True, **kwargs) -> dict:
        """
        Helper to execute HTTP requests with Operation-ID, Auth, and Retries.
        """
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self._get_auth_token()}"
        # Distributed transaction gap fix: Generate Operation ID for tracing
        headers["X-Operation-Id"] = str(uuid.uuid4())
        
        max_retries = 3 if is_read else 0
        last_exc = None
        
        for attempt in range(max_retries):
            try:
                response = self._client.request(
                    method, 
                    f"{self.base_url}{endpoint}", 
                    headers=headers, 
                    **kwargs
                )
                response.raise_for_status()
                return response.json()
            except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.HTTPStatusError) as e:
                last_exc = e
                logger.warning(f"PMS Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                if not is_read or attempt == max_retries - 1:
                    break
                # Exponential backoff could be added here with time.sleep
                
        raise ConnectionError(f"Failed to communicate with PMS after {max_retries} retries.") from last_exc

    # --- PMSInterface Implementation ---

    def search_guests(self, name: str) -> list[Guest]:
        data = self._request("GET", "/guests", params={"name": name})
        return [Guest(**g) for g in data.get("guests", [])]

    def get_reservation(self, reservation_id: str | None = None, guest_name: str | None = None) -> list[Reservation]:
        params = {}
        if reservation_id: params["reservation_id"] = reservation_id
        if guest_name: params["guest_name"] = guest_name
        data = self._request("GET", "/reservations", params=params)
        return [Reservation(**r) for r in data.get("reservations", [])]

    def get_arrivals(self, on_date: date) -> list[Reservation]:
        data = self._request("GET", "/reservations", params={"arrival": on_date.isoformat(), "status": "reserved"})
        return [Reservation(**r) for r in data.get("reservations", [])]

    def get_departures(self, on_date: date) -> list[Reservation]:
        data = self._request("GET", "/reservations", params={"departure": on_date.isoformat(), "status": "in_house"})
        return [Reservation(**r) for r in data.get("reservations", [])]

    def get_room(self, room_number: str) -> Room | None:
        try:
            data = self._request("GET", f"/rooms/{room_number}")
            return Room(**data)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    def get_rooms(self, status: RoomStatus | None = None) -> list[Room]:
        params = {"status": status.value if status else None}
        data = self._request("GET", "/rooms", params=params)
        return [Room(**r) for r in data.get("rooms", [])]

    def mark_room_clean(self, room_number: str) -> Room:
        # is_read=False enforces no retries on writes
        data = self._request("PUT", f"/rooms/{room_number}/status", json={"status": "CLEAN"}, is_read=False)
        return Room(**data)

    def get_incidents(self, status: str | None = None) -> list[Incident]:
        data = self._request("GET", "/incidents", params={"status": status})
        return [Incident(**i) for i in data.get("incidents", [])]

    def create_incident(self, room_number: str | None, incident_type: str, description: str) -> Incident:
        payload = {"type": incident_type, "description": description}
        if room_number: payload["room_number"] = room_number
        data = self._request("POST", "/incidents", json=payload, is_read=False)
        return Incident(**data)

    def resolve_incident(self, incident_id: str) -> Incident:
        data = self._request("PUT", f"/incidents/{incident_id}/resolve", is_read=False)
        return Incident(**data)