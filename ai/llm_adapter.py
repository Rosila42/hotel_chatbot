from __future__ import annotations


class LLMAdapter:
    """Thin provider boundary. No provider is configured in deterministic V2 yet."""

    def __init__(self, model: str | None = None) -> None:
        self.model = model

    def complete(self, prompt: str, system: str | None = None, max_tokens: int = 1000) -> str:
        raise RuntimeError("No LLM provider is configured for this V2 build")
