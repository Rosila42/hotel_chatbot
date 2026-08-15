from datetime import date

from integrations.pms.mock_adapter import MockPMSAdapter
from models.pms import RoomStatus
from services.pms_service import PMSService


def test_get_arrivals_uses_mock_pms():
    service = PMSService(MockPMSAdapter())
    arrivals = service.get_arrivals(date.today())
    assert arrivals
    assert arrivals[0].room_number == "214"


def test_not_ready_arrivals_is_composed_by_pms_service():
    service = PMSService(MockPMSAdapter())
    rooms = service.get_room_status(filter_name="not_ready_arrivals")
    assert rooms
    assert rooms[0].status != RoomStatus.READY


def test_mark_room_clean_changes_status():
    service = PMSService(MockPMSAdapter())
    room = service.mark_room_clean("214")
    assert room.status == RoomStatus.READY
