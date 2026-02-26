from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer

DEFAULT_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # 384-dim


_model: SentenceTransformer | None = None


def get_model(model_name: str = DEFAULT_EMBED_MODEL) -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(model_name)
    return _model


def embed_text(text: str, model_name: str = DEFAULT_EMBED_MODEL) -> np.ndarray:
    """
    Returns a float32 numpy vector. We normalize so cosine similarity is just dot().
    """
    model = get_model(model_name)
    vec = model.encode([text], normalize_embeddings=True)[0]
    return np.asarray(vec, dtype=np.float32)


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    """
    Cosine similarity between two vectors.
    If vectors are normalized, this is just dot(a,b), but we keep it safe.
    """
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0.0:
        return 0.0
    return float(np.dot(a, b) / denom)