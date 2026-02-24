from __future__ import annotations

DEFAULT_SYSTEM_PROMPT_V1 = """You are Molly, a helpful assistant.
Be friendly, clear, and pragmatic.
When uncertain, say so briefly and suggest how to verify.
Keep answers concise unless the user asks for depth.
"""
DEFAULT_PROMPT_VERSION = 1

TITLE_SYSTEM = """You generate short, useful conversation titles.
Return ONLY the title. No quotes, no punctuation at the end."""
SUMMARY_SYSTEM = """You maintain a running summary of a conversation.
Return ONLY the updated summary. No preamble."""

def make_title_prompt(messages: list[str]) -> str:
    joined = "\n".join(messages)
    return f"Create a short title (3-7 words) for this conversation:\n{joined}"

def make_summary_prompt(previous_summary: str | None, new_messages: list[str]) -> str:
    prev = previous_summary.strip() if previous_summary else ""
    joined = "\n".join(new_messages)
    if prev:
        return f"Previous summary:\n{prev}\n\nNew messages:\n{joined}\n\nUpdate the summary to include the new messages."
    return f"New messages:\n{joined}\n\nWrite a concise summary."