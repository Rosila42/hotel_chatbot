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
    # The parser output is data only; no identity, permission, or service dependency is involved.


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
