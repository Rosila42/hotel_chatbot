from datetime import date

from core.parser import DeterministicParser
from models.commands import CommandRequest


def build_parser() -> DeterministicParser:
    return DeterministicParser(today_provider=lambda: date(2026, 8, 23))


def test_parser_contract_returns_command_request_for_supported_intent():
    request = build_parser().parse("Who is arriving today?")

    assert isinstance(request, CommandRequest)
    assert request == CommandRequest("GET_ARRIVALS", {"date": "2026-08-23"})


def test_parser_contract_returns_none_for_unknown_intent():
    assert build_parser().parse("tell me something random") is None


def test_parser_does_not_authorize_or_execute():
    request = build_parser().parse("enable morning arrival check")

    assert request is not None
    assert request.name == "ENABLE_AUTOMATION"
    assert request.parameters == {"automation_id": "MORNING_ARRIVAL_CHECK"}


def test_parser_incident_list_is_not_misclassified_as_create_incident():
    request = build_parser().parse("show open incidents")

    assert request == CommandRequest("GET_INCIDENTS", {"status": "OPEN"})


def test_parser_create_incident_stays_a_command_request():
    request = build_parser().parse("The AC in room 214 is broken")

    assert request is not None
    assert request.name == "CREATE_INCIDENT"
    assert request.parameters["room_number"] == "214"
    assert request.parameters["incident_type"] == "MAINTENANCE"


def test_parser_preserves_automation_precedence_over_arrival_language():
    request = build_parser().parse("run morning arrival check")

    assert request == CommandRequest(
        "RUN_AUTOMATION",
        {"automation_id": "MORNING_ARRIVAL_CHECK"},
    )


def test_parser_accepts_arrival_aliases():
    assert build_parser().parse("show today's check ins") == CommandRequest(
        "GET_ARRIVALS", {"date": "2026-08-23"}
    )


def test_parser_accepts_departure_aliases():
    assert build_parser().parse("who is leaving tomorrow?") == CommandRequest(
        "GET_DEPARTURES", {"date": "2026-08-24"}
    )


def test_parser_accepts_relative_departure_date():
    assert build_parser().parse("show yesterday's departures") == CommandRequest(
        "GET_DEPARTURES", {"date": "2026-08-22"}
    )


def test_parser_accepts_iso_date():
    assert build_parser().parse("arrivals for 2026-08-25") == CommandRequest(
        "GET_ARRIVALS", {"date": "2026-08-25"}
    )


def test_parser_extracts_guest_name_from_direct_search():
    assert build_parser().parse("find Maria Rossi") == CommandRequest(
        "SEARCH_GUEST", {"name": "Maria Rossi"}
    )


def test_parser_extracts_guest_name_after_guest_keyword():
    assert build_parser().parse("search guest Maria Rossi") == CommandRequest(
        "SEARCH_GUEST", {"name": "Maria Rossi"}
    )


def test_parser_accepts_booking_vocabulary_and_preserves_case():
    assert build_parser().parse("booking ABC-123") == CommandRequest(
        "GET_RESERVATION", {"reservation_id": "ABC-123"}
    )


def test_parser_extracts_guest_name_for_reservation_lookup():
    assert build_parser().parse("reservation for Maria Rossi") == CommandRequest(
        "GET_RESERVATION", {"guest_name": "Maria Rossi"}
    )


def test_parser_accepts_room_status_questions():
    assert build_parser().parse("is room 214 ready?") == CommandRequest(
        "GET_ROOM_STATUS", {"room_number": "214"}
    )


def test_parser_passive_dirty_room_question_remains_read_only():
    assert build_parser().parse("room 214 is dirty") == CommandRequest(
        "GET_ROOM_STATUS", {"room_number": "214"}
    )


def test_parser_accepts_mark_room_clean_variants():
    assert build_parser().parse("please mark room 214 clean") == CommandRequest(
        "MARK_ROOM_CLEAN", {"room_number": "214"}
    )


def test_parser_reports_housekeeping_incident_type():
    request = build_parser().parse("report a dirty room 214")

    assert request is not None
    assert request.name == "CREATE_INCIDENT"
    assert request.parameters["room_number"] == "214"
    assert request.parameters["incident_type"] == "HOUSEKEEPING"


def test_parser_accepts_operational_summary_aliases():
    assert build_parser().parse("give me today's summary") == CommandRequest(
        "GET_OPERATIONAL_SUMMARY", {"date": "2026-08-23"}
    )


def test_parser_accepts_common_faq_aliases():
    assert build_parser().parse("what time is breakfast?") == CommandRequest(
        "FAQ_SEARCH", {"query": "what time is breakfast?"}
    )

    assert build_parser().parse("do we have wifi?") == CommandRequest(
        "FAQ_SEARCH", {"query": "do we have wifi?"}
    )
