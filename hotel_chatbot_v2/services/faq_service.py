from __future__ import annotations


class FAQService:
    """Deterministic FAQ retrieval from an approved in-memory knowledge base for V1."""

    def __init__(self, entries: dict[str, str] | None = None) -> None:
        self.entries = entries or {
            "breakfast": "Breakfast is served from 06:30 to 10:30.",
            "checkout": "Standard checkout time is 12:00.",
            "wifi": "Wi-Fi is available to hotel guests. Ask Reception for the current access instructions.",
        }

    def search(self, query: str) -> dict:
        normalized = query.strip().lower()
        matches = [
            {"topic": key, "answer": answer}
            for key, answer in self.entries.items()
            if key in normalized
        ]
        return {"query": query, "matches": matches}
