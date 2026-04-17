from __future__ import annotations

import hashlib


def stable_hash_embedding(text: str, dims: int = 256) -> list[float]:
    """
    Deterministic embedding fallback (no external embeddings provider).
    """
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values = []
    for i in range(dims):
        b = digest[i % len(digest)]
        values.append((b / 255.0) * 2.0 - 1.0)
    return values

