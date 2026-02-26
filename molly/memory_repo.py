from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from molly.embeddings import embed_text, cosine_sim
from molly.models import MemoryEmbedding, MemoryItem


@dataclass
class MemoryHit:
    item: MemoryItem
    score: float


class MemoryRepo:
    """
    DB-backed memory store with in-process cosine similarity search.
    Stores embeddings as float32 bytes in MemoryEmbedding.vector.
    """

    def __init__(self, session: Session):
        self.session = session

    def add_memory(self, kind: str, text: str, salience: float = 1.0) -> MemoryItem:
        kind = (kind or "").strip()
        text = (text or "").strip()
        if not kind:
            raise ValueError("kind is required")
        if not text:
            raise ValueError("text is required")

        item = MemoryItem(
            kind=kind,
            text=text,
            salience=float(salience),
            created_at=datetime.utcnow(),
        )
        self.session.add(item)
        self.session.flush()  # ensures item.id exists

        vec = embed_text(f"{kind}: {text}")
        emb = MemoryEmbedding(
            memory_item_id=item.id,
            vector=vec.tobytes(),
        )
        self.session.add(emb)

        # If you have relationship wiring, this is nice to keep the object graph consistent
        try:
            item.embedding = emb  # type: ignore[attr-defined]
        except Exception:
            pass

        return item

    def search(
        self,
        query: str,
        top_k: int = 5,
        min_salience: float = 0.0,
    ) -> list[tuple[MemoryItem, float]]:
        query = (query or "").strip()
        if not query:
            return []

        qv = embed_text(query)

        # Load items + embedding rows. We'll be tolerant if relationship isn't present.
        items = (
            self.session.query(MemoryItem)
            .filter(MemoryItem.salience >= float(min_salience))
            .all()
        )

        scored: list[tuple[MemoryItem, float]] = []
        for item in items:
            emb: MemoryEmbedding | None = None

            # If relationship exists (preferred)
            if hasattr(item, "embedding"):
                emb = getattr(item, "embedding", None)

            # Fallback: query embedding by FK
            if emb is None:
                emb = (
                    self.session.query(MemoryEmbedding)
                    .filter(MemoryEmbedding.memory_item_id == item.id)
                    .one_or_none()
                )

            if emb is None or emb.vector is None:
                continue

            v = np.frombuffer(emb.vector, dtype=np.float32)
            score = cosine_sim(qv, v)
            scored.append((item, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[: max(1, int(top_k))]

    def touch_last_used(self, ids: Iterable[int]) -> None:
        ids = [int(x) for x in ids]
        if not ids:
            return
        (
            self.session.query(MemoryItem)
            .filter(MemoryItem.id.in_(ids))
            .update({MemoryItem.last_used_at: func.now()}, synchronize_session=False)
        )