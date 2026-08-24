import pytest
import httpx
from datetime import date

from pms_adapters.real_pms_adapter import RealPMSAdapter

# --- 1. Create a Mock HTTP Handler ---
def mock_pms_handler(request: httpx.Request) -> httpx.Response:
    """Routes incoming requests to the mock PMS API."""
    
    # Verify the adapter sent the right headers
    assert "Authorization" in request.headers
    assert "X-Operation-Id" in request.headers

    # Route to the correct endpoint
    if request.url.path == "/reservations":
        return httpx.Response(200, json={"reservations": [{"reservation_id": "res-1", "guest_name": "John Martin"}]})
    elif request.url.path.startswith("/rooms/") and request.url.path.endswith("/status"):
        return httpx.Response(200, json={"room_number": "214", "status": "CLEAN", "room_type": "double"})
    
    return httpx.Response(404, json={"detail": "Not Found"})

# --- 2. Tests ---

@pytest.fixture
def mock_pms_adapter():
    """Creates a RealPMSAdapter routed to our mock handler instead of the internet."""
    transport = httpx.MockTransport(mock_pms_handler)
    client = httpx.Client(transport=transport, base_url="http://testserver")
    # Pass base_url="" so the adapter doesn't prepend "https://api.pms.com/v1"
    return RealPMSAdapter(base_url="", client=client)

    '''
@pytest.fixture
def mock_pms_adapter():
    """Creates a RealPMSAdapter routed to our mock handler instead of the internet."""
    transport = httpx.MockTransport(mock_pms_handler)
    client = httpx.Client(transport=transport, base_url="http://testserver")
    return RealPMSAdapter(client=client)
    '''
    
def test_adapter_get_arrivals(mock_pms_adapter):
    """Test that the adapter can fetch arrivals from the mock HTTP server."""
    arrivals = mock_pms_adapter.get_arrivals(date(2026, 8, 25))
    
    assert len(arrivals) == 1
    assert arrivals[0].guest_name == "John Martin"

def test_adapter_mark_room_clean(mock_pms_adapter):
    """Test that the adapter can perform write operations against the mock HTTP server."""
    updated_room = mock_pms_adapter.mark_room_clean("214")
    
    assert updated_room.room_number == "214"
    assert updated_room.status == "CLEAN"

def test_adapter_sends_operation_id(mock_pms_adapter):
    """Test that the distributed transaction header is present."""
    # The mock_pms_handler function asserts that the header exists. 
    # If it doesn't, it will raise an AssertionError.
    try:
        mock_pms_adapter.get_arrivals(date(2026, 8, 25))
        assert True
    except AssertionError:
        pytest.fail("Adapter did not send X-Operation-Id header!")