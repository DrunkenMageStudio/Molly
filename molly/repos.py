from __future__ import annotations

from sqlalchemy.orm import Session

from molly.models import AppMeta, Conversation, Message
from molly.prompts import DEFAULT_SYSTEM_PROMPT_V1, DEFAULT_PROMPT_VERSION
from sqlalchemy.sql import func

class AppMetaRepo:
    def __init__(self, session: Session):
        self.session = session

    def upsert(self, key: str, value: str) -> None:
        row = self.session.get(AppMeta, key)
        if row is None:
            row = AppMeta(key=key, value=value)
            self.session.add(row)
        else:
            row.value = value

    def get(self, key: str) -> str | None:
        row = self.session.get(AppMeta, key)
        return None if row is None else row.value


class ConversationRepo:
    def __init__(self, session: Session):
        self.session = session

    def create(self, title: str | None = None) -> Conversation:
        convo = Conversation(
            title=title,
            system_prompt=DEFAULT_SYSTEM_PROMPT_V1,
            prompt_version=DEFAULT_PROMPT_VERSION,
        )
        self.session.add(convo)
        self.session.flush()  # so ID is available immediately
        return convo

    def get(self, convo_id: str) -> Conversation | None:
        return self.session.get(Conversation, convo_id)
    
    def set_prompt(self, convo_id: str, prompt: str, version: int | None = None) -> bool:
        convo = self.session.get(Conversation, convo_id)
        if convo is None:
            return False
        convo.system_prompt = prompt
        if version is not None:
            convo.prompt_version = version
        return True
    
    def set_title(self, convo_id: str, title: str) -> bool:
        convo = self.session.get(Conversation, convo_id)
        if convo is None:
            return False
        convo.title = title
        return True

    def set_summary(self, convo_id: str, summary: str) -> bool:
        convo = self.session.get(Conversation, convo_id)
        if convo is None:
            return False
        convo.summary = summary
        convo.summary_updated_at = func.now()
        return True


class MessageRepo:
    def __init__(self, session: Session):
        self.session = session

    def tail_for_conversation(self, conversation_id: str, limit: int = 20) -> list[Message]:
        rows = (
            self.session.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.id.desc())
            .limit(limit)
            .all()
        )
        return list(reversed(rows))

    def add(self, conversation_id: str, role: str, content: str) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )
        self.session.add(msg)
        return msg

    def list_for_conversation(self, conversation_id: str) -> list[Message]:
        return (
            self.session.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .all()
        )