from __future__ import annotations

import logging
import uuid

from app.utils.text import stable_hash_embedding

logger = logging.getLogger(__name__)


class VectorStoreError(RuntimeError):
    pass


class VectorStore:
    async def add(
        self,
        *,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID | None,
        text: str,
        metadata: dict,
        memory_scope: str = "user",
        context_key: str | None = None,
    ) -> str:
        raise NotImplementedError

    async def query(
        self,
        *,
        user_id: uuid.UUID,
        query: str,
        top_k: int,
        memory_scope: str = "user",
        context_key: str | None = None,
    ) -> list[dict]:
        raise NotImplementedError


class InMemoryVectorStore(VectorStore):
    def __init__(self) -> None:
        self._items: list[dict] = []

    async def add(
        self,
        *,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID | None,
        text: str,
        metadata: dict,
        memory_scope: str = "user",
        context_key: str | None = None,
    ) -> str:
        _id = str(uuid.uuid4())
        self._items.append(
            {
                "id": _id,
                "user_id": str(user_id),
                "conversation_id": str(conversation_id) if conversation_id else None,
                "memory_scope": memory_scope,
                "context_key": context_key,
                "text": text,
                "embedding": stable_hash_embedding(text),
                "metadata": metadata,
            }
        )
        return _id

    async def query(
        self,
        *,
        user_id: uuid.UUID,
        query: str,
        top_k: int,
        memory_scope: str = "user",
        context_key: str | None = None,
    ) -> list[dict]:
        q = stable_hash_embedding(query)

        def dot(a: list[float], b: list[float]) -> float:
            return float(sum(x * y for x, y in zip(a, b, strict=False)))

        hits = []
        for item in self._items:
            if item["user_id"] != str(user_id):
                continue
            if item["memory_scope"] != memory_scope:
                continue
            if item["context_key"] != context_key:
                continue
            score = dot(q, item["embedding"])
            hits.append({"id": item["id"], "text": item["text"], "score": score, "metadata": item["metadata"]})
        hits.sort(key=lambda x: x["score"], reverse=True)
        return hits[:top_k]


class ChromaVectorStore(VectorStore):
    def __init__(self, *, persist_dir: str) -> None:
        try:
            import chromadb  # type: ignore
        except Exception as exc:  # noqa: BLE001
            raise VectorStoreError("chromadb is not installed.") from exc

        self._client = chromadb.PersistentClient(path=persist_dir)
        self._collection = self._client.get_or_create_collection(name="memories")

    async def add(
        self,
        *,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID | None,
        text: str,
        metadata: dict,
        memory_scope: str = "user",
        context_key: str | None = None,
    ) -> str:
        _id = str(uuid.uuid4())
        meta = {
            "id": _id,
            "user_id": str(user_id),
            "conversation_id": str(conversation_id) if conversation_id else None,
            "memory_scope": memory_scope,
            "context_key": context_key,
            **(metadata or {}),
        }
        emb = stable_hash_embedding(text)
        self._collection.add(ids=[_id], documents=[text], metadatas=[meta], embeddings=[emb])
        return _id

    async def query(
        self,
        *,
        user_id: uuid.UUID,
        query: str,
        top_k: int,
        memory_scope: str = "user",
        context_key: str | None = None,
    ) -> list[dict]:
        emb = stable_hash_embedding(query)
        where: dict[str, str | None] = {"user_id": str(user_id), "memory_scope": memory_scope}
        where["context_key"] = context_key
        res = self._collection.query(
            query_embeddings=[emb],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        hits = []
        for doc, meta, dist in zip(docs, metas, dists, strict=False):
            score = float(-dist) if dist is not None else 0.0
            hits.append({"id": meta.get("id", ""), "text": doc, "score": score, "metadata": meta})
        return hits
