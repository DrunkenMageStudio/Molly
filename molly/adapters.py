from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ChatMessage:
    role: str   # "system" | "user" | "assistant"
    content: str


class ModelAdapter(Protocol):
    name: str

    def generate(self, messages: list[ChatMessage]) -> str:
        """Return the assistant's next message."""
        ...


class DummyAdapter:
    name = "dummy"

    def generate(self, messages: list[ChatMessage]) -> str:
        # Respond to the most recent user message
        last_user = next((m.content for m in reversed(messages) if m.role == "user"), "")
        return f"Acknowledged: {last_user}"