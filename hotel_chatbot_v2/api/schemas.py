from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str | None = None
    shift: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    success: bool
    message: str
    command: str | None = None
    data: object | None = None
