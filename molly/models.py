from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    LargeBinary,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class MemoryItem(Base):
    __tablename__ = "memory_item"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(String(50), nullable=False)  # preference/project/fact/etc
    text: Mapped[str] = mapped_column(Text, nullable=False)

    salience: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    embedding: Mapped["MemoryEmbedding | None"] = relationship(
        back_populates="memory_item",
        cascade="all, delete-orphan",
        uselist=False,
    )


class MemoryEmbedding(Base):
    __tablename__ = "memory_embedding"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    memory_item_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("memory_item.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # Store float32 bytes (e.g., numpy.ndarray.astype(np.float32).tobytes())
    vector: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    memory_item: Mapped["MemoryItem"] = relationship(back_populates="embedding")


class AppMeta(Base):
    """
    Tiny table for bootstrapping: records schema/app facts.
    Useful for sanity checks and future migrations.
    """

    __tablename__ = "app_meta"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Conversation(Base):
    __tablename__ = "conversation"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)

    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_version: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1)

    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
    )


class Message(Base):
    __tablename__ = "message"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    conversation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conversation.id", ondelete="CASCADE"),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(String(32), nullable=False)  # user | assistant | system
    content: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")