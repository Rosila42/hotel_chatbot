from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Type

from pydantic import BaseModel, ValidationError


class OperationType(str, Enum):
    READ = "READ"
    WRITE = "WRITE"
    AUTOMATION = "AUTOMATION"


class ConfirmationPolicy(str, Enum):
    NONE = "NONE"
    RECOMMENDED = "RECOMMENDED"
    REQUIRED = "REQUIRED"


class ResultKind(str, Enum):
    SUCCESS = "SUCCESS"
    DENIED = "DENIED"
    INVALID_PARAMS = "INVALID_PARAMS"
    AWAITING_CONFIRMATION = "AWAITING_CONFIRMATION"
    UNKNOWN_COMMAND = "UNKNOWN_COMMAND"
    FAILED = "FAILED"


@dataclass(frozen=True)
class CommandDefinition:
    name: str
    description: str
    operation_type: OperationType
    permission: str | None
    confirmation: ConfirmationPolicy = ConfirmationPolicy.NONE
    params_model: Type[BaseModel] | None = None

    def validate(self, parameters: dict[str, Any]) -> list[str]:
        if self.params_model is None:
            return []
        try:
            self.params_model.model_validate(parameters)
        except ValidationError as exc:
            return [self._format_validation_error(error) for error in exc.errors()]
        return []

    @staticmethod
    def _format_validation_error(error: dict[str, Any]) -> str:
        location = ".".join(str(item) for item in error.get("loc", ())) or "parameters"
        return f"{location}: {error.get('msg', 'invalid value')}"


@dataclass(frozen=True)
class CommandRequest:
    name: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CommandResult:
    kind: ResultKind
    message: str
    data: Any = None
    command: str | None = None

    @property
    def success(self) -> bool:
        """Backward-compatible boolean view for existing API clients/tests."""
        return self.kind is ResultKind.SUCCESS
