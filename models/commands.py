from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class OperationType(str, Enum):
    READ = "READ"
    WRITE = "WRITE"
    AUTOMATION = "AUTOMATION"


class ConfirmationPolicy(str, Enum):
    NONE = "NONE"
    RECOMMENDED = "RECOMMENDED"
    REQUIRED = "REQUIRED"


@dataclass(frozen=True)
class CommandDefinition:
    name: str
    description: str
    operation_type: OperationType
    permission: str | None
    confirmation: ConfirmationPolicy = ConfirmationPolicy.NONE
    handler: Callable[..., Any] | None = field(default=None, compare=False)


@dataclass(frozen=True)
class CommandRequest:
    name: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CommandResult:
    success: bool
    message: str
    data: Any = None
    command: str | None = None
