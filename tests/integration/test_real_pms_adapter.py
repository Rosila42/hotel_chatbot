import httpx
import pytest
from datetime import date

from pms_adapters.real_pms_adapter import RealPMSAdapter


def mock_pms_handler(request: httpx.Request) -> httpx.Response:
    """Route incoming requests to a deterministic mock PMS API."""
    assert "Authorization" in request.headers
    assert "X-Operation-Id" in request.headers

    if request.url.path == "/reservations":
        return httpx.Response(
            200,
            json={
                "reservations": [
                    {
                        "reservation_id": "res-1",
                        "guest_id": "g1",
                        "guest_name": "John Martin",
                        "room_number": "214",
                        "arrival": "2026-08-25",
                        "departure": "2026-08-28",
                        "status": "CONFIRMED",
                    }
                ]
            },
        )
    if request.url.path.startswith("/rooms/") and request.url.path.endswith("/status"):
        return httpx.Response(
            200,
            json={"room_number": "214", "status": "CLEAN", "room_type": "double"},
        )
    if request.url.path == "/rooms/404":
        return httpx.Response(404, json={"detail": "Not Found"})

    return httpx.Response(404, json={"detail": "Not Found"})


@pytest.fixture
def mock_pms_adapter():
    transport = httpx.MockTransport(mock_pms_handler)
    client = httpx.Client(transport=transport, base_url="http://testserver")
    return RealPMSAdapter(base_url="", client=client)


def test_adapter_get_arrivals(mock_pms_adapter):
    arrivals = mock_pms_adapter.get_arrivals(date(2026, 8, 25))

    assert len(arrivals) == 1
    assert arrivals[0].guest_name == "John Martin"
    assert arrivals[0].reservation_id == "res-1"
    assert arrivals[0].room_number == "214"


def test_adapter_mark_room_clean(mock_pms_adapter):
    updated_room = mock_pms_adapter.mark_room_clean("214")

    assert updated_room.room_number == "214"
    assert updated_room.status == "CLEAN"


def test_adapter_missing_room_returns_none(mock_pms_adapter):
    assert mock_pms_adapter.get_room("404") is None


def test_adapter_sends_operation_id(mock_pms_adapter):
    mock_pms_adapter.get_arrivals(date(2026, 8, 25))
