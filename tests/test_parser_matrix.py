from datetime import date

import pytest

from core.commands import CommandRegistry
from core.parser import DeterministicParser
from core.permissions import PermissionService
from models.commands import CommandRequest


PARSER_CASES = [
    ("help", CommandRequest("HELP")),
    ("system status", CommandRequest("GET_SYSTEM_STATUS")),
    ("find Maria Rossi", CommandRequest("SEARCH_GUEST", {"name": "Maria Rossi"})),
    ("booking ABC-123", CommandRequest("GET_RESERVATION", {"reservation_id": "ABC-123"})),
    ("arrivals for 2026-08-25", CommandRequest("GET_ARRIVALS", {"date": "2026-08-25"})),
    ("who is leaving tomorrow?", CommandRequest("GET_DEPARTURES", {"date": "2026-08-24"})),
    ("is room 214 ready?", CommandRequest("GET_ROOM_STATUS", {"room_number": "214"})),
    ("which rooms are not ready?", CommandRequest("GET_ROOM_STATUS", {"filter": "not_ready"})),
    ("mark room 214 clean", CommandRequest("MARK_ROOM_CLEAN", {"room_number": "214"})),
    ("show open incidents", CommandRequest("GET_INCIDENTS", {"status": "OPEN"})),
    ("report a dirty room 214", CommandRequest("CREATE_INCIDENT", {
        "room_number": "214",
        "incident_type": "HOUSEKEEPING",
        "description": "report a dirty room 214",
    })),
    ("resolve incident 42", CommandRequest("RESOLVE_INCIDENT", {"incident_id": "42"})),
    ("give me today's summary", CommandRequest("GET_OPERATIONAL_SUMMARY", {"date": "2026-08-23"})),
    ("what time is breakfast?", CommandRequest("FAQ_SEARCH", {"query": "what time is breakfast?"})),
    ("list automations", CommandRequest("LIST_AUTOMATIONS")),
    ("enable automation NIGHT_AUDIT", CommandRequest("ENABLE_AUTOMATION", {"automation_id": "NIGHT_AUDIT"})),
    ("disable workflow NIGHT_AUDIT", CommandRequest("DISABLE_AUTOMATION", {"automation_id": "NIGHT_AUDIT"})),
    ("run automation NIGHT_AUDIT", CommandRequest("RUN_AUTOMATION", {"automation_id": "NIGHT_AUDIT"})),
    ("show workflow NIGHT_AUDIT status", CommandRequest("GET_AUTOMATION_STATUS", {"automation_id": "NIGHT_AUDIT"})),
    ("show automation NIGHT_AUDIT history", CommandRequest("GET_AUTOMATION_HISTORY", {"automation_id": "NIGHT_AUDIT"})),
]


def build_parser() -> DeterministicParser:
    return DeterministicParser(today_provider=lambda: date(2026, 8, 23))


@pytest.mark.parametrize("text, expected", PARSER_CASES)
def test_every_catalog_command_has_a_parser_example(text: str, expected: CommandRequest):
    assert build_parser().parse(text) == expected


def test_every_matrix_command_exists_in_authoritative_registry():
    registry = CommandRegistry(PermissionService())
    names = {request.name for _, request in PARSER_CASES}

    assert names == {command.name for command in registry.all()}


def test_unknown_text_returns_no_command_request():
    assert build_parser().parse("tell me a joke about the weather") is None


def test_parser_matrix_output_contains_only_command_request_data():
    for _, request in PARSER_CASES:
        assert set(vars(request)) == {"name", "parameters"}
        assert isinstance(request.name, str)
        assert isinstance(request.parameters, dict)


def test_parser_matrix_cannot_authorize_or_execute():
    for _, request in PARSER_CASES:
        assert not hasattr(request, "permission")
        assert not hasattr(request, "confirmation")
        assert not hasattr(request, "identity")
