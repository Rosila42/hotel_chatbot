import json

from ai.llm_parser import LLMParser
from models.commands import CommandRequest


class FakeAdapter:
    def __init__(self, payload: str) -> None:
        self.payload = payload
        self.calls = 0
        self.last_prompt = None
        self.last_system = None

    def complete(self, prompt: str, system=None, max_tokens=500) -> str:
        self.calls += 1
        self.last_prompt = prompt
        self.last_system = system
        return self.payload


def build_parser(payload: str) -> tuple[LLMParser, FakeAdapter]:
    adapter = FakeAdapter(payload)
    parser = LLMParser(
        adapter,
        allowed_commands={"GET_ARRIVALS", "CREATE_INCIDENT", "HELP"},
    )
    return parser, adapter


def test_llm_parser_returns_command_request_for_valid_json():
    parser, _ = build_parser(
        json.dumps({"command": "GET_ARRIVALS", "parameters": {"date": "2026-08-23"}})
    )

    assert parser.parse("who is arriving today?") == CommandRequest(
        "GET_ARRIVALS", {"date": "2026-08-23"}
    )


def test_llm_parser_normalizes_command_name():
    parser, _ = build_parser(json.dumps({"command": "help", "parameters": {}}))

    assert parser.parse("help") == CommandRequest("HELP")


def test_llm_parser_rejects_unknown_command():
    parser, _ = build_parser(json.dumps({"command": "DELETE_ALL_ROOMS", "parameters": {}}))

    assert parser.parse("do something dangerous") is None


def test_llm_parser_rejects_extra_policy_fields():
    parser, _ = build_parser(
        json.dumps(
            {
                "command": "CREATE_INCIDENT",
                "parameters": {"room_number": "214"},
                "permission": "admin",
                "confirm": True,
            }
        )
    )

    assert parser.parse("report an issue in room 214") is None


def test_llm_parser_rejects_non_object_parameters():
    parser, _ = build_parser(json.dumps({"command": "HELP", "parameters": []}))

    assert parser.parse("help") is None


def test_llm_parser_rejects_non_json_output():
    parser, _ = build_parser("Here is the command: GET_ARRIVALS")

    assert parser.parse("who arrives?") is None


def test_llm_parser_has_no_authorization_or_execution_state():
    parser, _ = build_parser(json.dumps({"command": "CREATE_INCIDENT", "parameters": {}}))

    request = parser.parse("report issue")
    assert request is not None
    assert not hasattr(request, "permission")
    assert not hasattr(request, "identity")
    assert not hasattr(request, "confirmation")
    assert not hasattr(parser, "executor")
    assert not hasattr(parser, "pms")


def test_llm_parser_does_not_require_a_provider_specific_dependency():
    parser, adapter = build_parser(json.dumps({"command": "HELP", "parameters": {}}))

    request = parser.parse("commands")

    assert request == CommandRequest("HELP")
    assert adapter.calls == 1
    assert "JSON" in adapter.last_system
