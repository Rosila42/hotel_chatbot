from __future__ import annotations


class AIService:
    """Optional AI boundary. Core V1 does not require this service."""

    def __init__(self, adapter=None):
        self.adapter = adapter

    @property
    def enabled(self) -> bool:
        return self.adapter is not None

    def interpret(self, text: str):
        if not self.adapter:
            raise RuntimeError("AI is not configured")
        return self.adapter.complete(text)
