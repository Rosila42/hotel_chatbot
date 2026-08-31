from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str | None = None
    shift: str | None = None


class PermissionInfo(BaseModel):
    allowed: bool
    role: str
    allowed_roles: list[str] = Field(default_factory=list)


class ConfirmationInfo(BaseModel):
    state: str


class ChatResponse(BaseModel):
    session_id: str
    success: bool
    message: str
    command: str | None = None
    parameters: dict[str, Any] | None = None
    data: object | None = None
    parser_source: str | None = None
    permission: PermissionInfo | None = None
    confirmation: ConfirmationInfo | None = None
    pms_adapter: str | None = None
    state_before: str | None = None
    state_after: str | None = None
    audit_recorded: bool | None = None
