from __future__ import annotations

import json
from typing import Protocol

from models.commands import CommandRequest


class LLMCompletionAdapter(Protocol):
    """Minimal provider boundary required by LLMParser."""

    def complete(self, prompt: str, system: str | None = None, max_tokens: int = 500) -> str:
        ...


class LLMParser:
    """Untrusted LLM-to-CommandRequest interpretation adapter.

    The parser never authorizes, confirms, executes, or calls PMS/automation services.
    It accepts only strict JSON containing a known command name and an object of
    parameters. Parameter/business-policy validation remains in ChatRouter.
    """

    def __init__(self, adapter: LLMCompletionAdapter, allowed_commands: set[str]) -> None:
        self._adapter = adapter
        self._allowed_commands = {name.upper() for name in allowed_commands}

    def parse(self, text: str) -> CommandRequest | None:
        if not text.strip():
            return None

        try:
            raw = self._adapter.complete(self._build_prompt(text), system=self._system_prompt())
            payload = json.loads(raw)
        except (TypeError, ValueError, json.JSONDecodeError):
            return None

        if not isinstance(payload, dict):
            return None
        if set(payload) != {"command", "parameters"}:
            return None

        command = payload["command"]
        parameters = payload["parameters"]
        if not isinstance(command, str) or not isinstance(parameters, dict):
            return None

        command_name = command.strip().upper()
        if command_name not in self._allowed_commands:
            return None

        return CommandRequest(command_name, parameters)

    @staticmethod
    def _system_prompt() -> str:
        return (
            "Return exactly one JSON object with exactly these keys: "
            '"command" and "parameters". '
            'The command must be one of the supplied allowed commands. '
            'Do not include markdown, explanation, permissions, confirmation, identity, '
            'execution instructions, or service calls. Parameters must be a JSON object.'
        )

    @staticmethod
    def _build_prompt(text: str) -> str:
        return f"Interpret this hotel staff request as one structured command:\n{text}"
