from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

from hotel_chatbot_v2.core.permissions import Identity


@dataclass
class ChatSession:
    session_id: str
    identity: Identity
    shift: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    history: list[dict[str, str]] = field(default_factory=list)
    pending_command: dict | None = None

    @classmethod
    def create(cls, identity: Identity, shift: str | None = None) -> "ChatSession":
        return cls(str(uuid4()), identity, shift)

    def add_message(self, role: str, content: str) -> None:
        self.history.append({"role": role, "content": content})
        self.history = self.history[-50:]

    def set_pending(self, command: str, parameters: dict) -> None:
        self.pending_command = {"command": command, "parameters": parameters}

    def clear_pending(self) -> None:
        self.pending_command = None
