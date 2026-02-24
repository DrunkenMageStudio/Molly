from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams


@dataclass(frozen=True)
class QdrantSettings:
    url: str = "http://127.0.0.1:6333"
    collection: str = "molly_memories"
    vector_size: int = 384  # all-MiniLM-L6-v2
    distance: Distance = Distance.COSINE


def get_qdrant_client(cfg: QdrantSettings) -> QdrantClient:
    return QdrantClient(url=cfg.url)


def ensure_collection(client: QdrantClient, cfg: QdrantSettings) -> None:
    existing = {c.name for c in client.get_collections().collections}
    if cfg.collection in existing:
        return

    client.create_collection(
        collection_name=cfg.collection,
        vectors_config=VectorParams(size=cfg.vector_size, distance=cfg.distance),
    )