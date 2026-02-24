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

import httpx
from molly.config import Settings

class LMStudioAdapter:
    name = "lmstudio"

    def __init__(self, settings: Settings):
        self.settings = settings

    def generate(self, messages: list[ChatMessage]) -> str:
        payload = {
            "model": self.settings.lmstudio.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": self.settings.lmstudio.temperature,
            "max_tokens": self.settings.lmstudio.max_tokens,
        }

        headers = {
            "Authorization": f"Bearer {self.settings.lmstudio.api_key}",
            "Content-Type": "application/json",
        }

        url = f"{self.settings.lmstudio.base_url}/chat/completions"

        with httpx.Client(timeout=60) as client:
            r = client.post(url, json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()

        return data["choices"][0]["message"]["content"].strip()
class DummyAdapter:
    name = "dummy"

    def generate(self, messages: list[ChatMessage]) -> str:
        # Respond to the most recent user message
        last_user = next((m.content for m in reversed(messages) if m.role == "user"), "")
        return f"Acknowledged: {last_user}"