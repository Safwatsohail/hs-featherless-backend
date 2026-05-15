from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import Select, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import Conversation, MemoryMetadata, Message

logger = logging.getLogger(__name__)

try:
    import chromadb
except Exception:  # pragma: no cover
    chromadb = None


@dataclass
class RetrievedMemory:
    id: str
    text: str
    score: float | None
    metadata: dict[str, Any]


class _InMemoryVectorStore:
    def __init__(self) -> None:
        self._items: list[dict[str, Any]] = []

    def add(self, *, item_id: str, text: str, metadata: dict[str, Any]) -> None:
        self._items.append({"id": item_id, "text": text, "metadata": metadata})

    def query(self, *, user_id: str, query: str, top_k: int) -> list[RetrievedMemory]:
        query_terms = set(query.lower().split())
        scored: list[RetrievedMemory] = []
        for item in self._items:
            if item["metadata"].get("user_id") != user_id:
                continue
            text_terms = set(item["text"].lower().split())
            overlap = len(query_terms & text_terms)
            if overlap == 0:
                continue
            scored.append(
                RetrievedMemory(
                    id=item["id"],
                    text=item["text"],
                    score=float(overlap),
                    metadata=item["metadata"],
                )
            )
        return sorted(scored, key=lambda memory: memory.score or 0, reverse=True)[:top_k]


class VectorMemoryStore:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.backend = self.settings.vector_backend
        self._fallback = _InMemoryVectorStore()
        self._collection = None

        if self.backend == "chroma" and chromadb is not None:
            try:
                client = chromadb.PersistentClient(path=str(self.settings.chroma_persist_dir))
                self._collection = client.get_or_create_collection(name="agent_memory")
            except Exception as exc:  # pragma: no cover
                logger.warning("Falling back to in-memory vector store: %s", exc)
                self.backend = "memory"

    def add(self, *, item_id: str, text: str, metadata: dict[str, Any]) -> None:
        # Ensure user preferences are properly tagged and shared across API keys
        if "user_id" in metadata:
            # For cross-API-key sharing, use email as primary identifier if available
            if "email" in metadata:
                metadata["shared_user_id"] = metadata["email"]
            else:
                metadata["shared_user_id"] = metadata["user_id"]
        
        # Auto-detect and tag user preferences
        text_lower = text.lower()
        if any(keyword in text_lower for keyword in ["prefer", "like", "want", "use", "color", "theme"]):
            metadata["is_preference"] = True
            metadata["preference_type"] = "user_setting"
        
        if self.backend == "chroma" and self._collection is not None:
            self._collection.add(ids=[item_id], documents=[text], metadatas=[metadata])
            return
        self._fallback.add(item_id=item_id, text=text, metadata=metadata)

    def query(self, *, user_id: str, query: str, top_k: int) -> list[RetrievedMemory]:
        if self.backend == "chroma" and self._collection is not None:
            # Support cross-API-key memory sharing - query both user_id and shared_user_id
            where_clause = {
                "$or": [
                    {"user_id": str(user_id)},
                    {"shared_user_id": str(user_id)}
                ]
            }
            
            # Boost preference matching for better user experience
            query_lower = query.lower()
            if any(pref in query_lower for pref in ["prefer", "like", "want", "color", "theme"]):
                # Add preference boost to query
                query = query + " user preferences settings"
            
            result = self._collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where_clause,
            )
            documents = result.get("documents", [[]])[0]
            ids = result.get("ids", [[]])[0]
            metadatas = result.get("metadatas", [[]])[0]
            distances = result.get("distances", [[]])[0] if result.get("distances") else []
            retrieved: list[RetrievedMemory] = []
            for index, document in enumerate(documents):
                metadata = metadatas[index] if index < len(metadatas) else {}
                # Boost preference items in results
                score = distances[index] if index < len(distances) else None
                if metadata.get("is_preference"):
                    score = (score or 0.5) * 0.8  # Boost preference matches
                
                retrieved.append(
                    RetrievedMemory(
                        id=ids[index],
                        text=document,
                        score=score,
                        metadata=metadata,
                    )
                )
            return retrieved
        return self._fallback.query(user_id=str(user_id), query=query, top_k=top_k)


vector_store = VectorMemoryStore()


class MemoryEngine:
    def __init__(
        self,
        session: AsyncSession | None = None,
        *,
        db: AsyncSession | None = None,
        vector_store: Any | None = None,
        short_term_max_messages: int | None = None,
    ) -> None:
        self.session = session or db
        if self.session is None:
            raise ValueError("MemoryEngine requires an AsyncSession")
        self.settings = get_settings()
        self.vector_store = vector_store or globals()["vector_store"]
        self.short_term_max_messages = short_term_max_messages or self.settings.short_term_max_messages

    async def get_or_create_conversation(
        self,
        *,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID | None,
        title: str | None = None,
        memory_scope: str = "user",
        context_key: str | None = None,
    ) -> Conversation:
        uid_str = str(user_id)
        if conversation_id is not None:
            existing = await self.session.get(Conversation, str(conversation_id))
            if existing is not None:
                return existing

        conversation = Conversation(
            user_id=uid_str,
            title=title,
            memory_scope=memory_scope,
            context_key=context_key,
        )
        self.session.add(conversation)
        await self.session.commit()
        await self.session.refresh(conversation)
        return conversation

    async def store_message(
        self,
        *,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
        content: str,
    ) -> Message:
        message = Message(
            conversation_id=str(conversation_id),
            user_id=str(user_id),
            role=role,
            content=content,
        )
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def get_short_term_memory(self, *, conversation_id: uuid.UUID, limit: int | None = None) -> list[Message]:
        stmt: Select[tuple[Message]] = (
            select(Message)
            .where(Message.conversation_id == str(conversation_id))
            .order_by(desc(Message.created_at))
            .limit(limit or self.short_term_max_messages)
        )
        result = await self.session.execute(stmt)
        messages = list(result.scalars().all())
        messages.reverse()
        return messages

    async def store_memory(
        self,
        *,
        user_id: uuid.UUID,
        text: str,
        kind: str,
        metadata: dict[str, Any],
        conversation_id: uuid.UUID | None = None,
        memory_scope: str = "user",
        context_key: str | None = None,
    ) -> MemoryMetadata:
        memory = MemoryMetadata(
            user_id=str(user_id),
            memory_scope=memory_scope,
            context_key=context_key,
            conversation_id=str(conversation_id) if conversation_id else None,
            kind=kind,
            data=metadata,
        )
        self.session.add(memory)
        await self.session.commit()
        await self.session.refresh(memory)

        await self.vector_store.add(
            user_id=user_id,
            conversation_id=conversation_id,
            text=text,
            memory_scope=memory_scope,
            context_key=context_key,
            metadata={
                "kind": kind,
                "memory_scope": memory_scope,
                "context_key": context_key,
                **metadata,
            },
        )
        return memory

    async def retrieve_memory(
        self,
        *,
        user_id: uuid.UUID,
        query: str,
        top_k: int | None = None,
        memory_scope: str = "user",
        context_key: str | None = None,
    ) -> list[RetrievedMemory]:
        # Check if the vector_store has the new async interface
        if hasattr(self.vector_store, '__class__') and self.vector_store.__class__.__name__ in ['InMemoryVectorStore', 'ChromaVectorStore']:
            # New async interface
            results = await self.vector_store.query(
                user_id=user_id,
                query=query,
                top_k=top_k or self.settings.vector_top_k,
                memory_scope=memory_scope,
                context_key=context_key,
            )
        else:
            # Old sync interface
            results = self.vector_store.query(
                user_id=str(user_id),
                query=query,
                top_k=top_k or self.settings.vector_top_k,
            )
        
        # Normalize dicts returned by VectorStore implementations into RetrievedMemory
        normalized: list[RetrievedMemory] = []
        for item in results:
            if isinstance(item, RetrievedMemory):
                normalized.append(item)
            elif isinstance(item, dict):
                normalized.append(
                    RetrievedMemory(
                        id=str(item.get("id", "")),
                        text=str(item.get("text", "")),
                        score=float(item.get("score") or 0.0),
                        metadata=item.get("metadata") or {},
                    )
                )
        return normalized

    async def short_term(self, *, conversation_id: uuid.UUID, user_id: uuid.UUID) -> list[Message]:
        return await self.get_short_term_memory(conversation_id=conversation_id, limit=self.short_term_max_messages)

    async def vector_retrieve(
        self,
        *,
        user_id: uuid.UUID,
        query: str,
        top_k: int,
        memory_scope: str = "user",
        context_key: str | None = None,
    ) -> list[dict]:
        items = await self.retrieve_memory(
            user_id=user_id,
            query=query,
            top_k=top_k,
            memory_scope=memory_scope,
            context_key=context_key,
        )
        normalized: list[dict] = []
        for item in items:
            if isinstance(item, RetrievedMemory):
                normalized.append(
                    {"id": item.id, "text": item.text, "score": item.score or 0.0, "metadata": item.metadata}
                )
            else:
                normalized.append(item)
        return normalized

    async def vector_store_text(
        self,
        *,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID | None,
        text: str,
        metadata: dict,
        memory_scope: str = "user",
        context_key: str | None = None,
    ) -> str:
        # Check if the vector_store has the new async interface (from vector_store.py)
        # or the old sync interface (from memory_engine.py)
        if hasattr(self.vector_store, '__class__') and self.vector_store.__class__.__name__ in ['InMemoryVectorStore', 'ChromaVectorStore']:
            # New async interface
            return await self.vector_store.add(
                user_id=user_id,
                conversation_id=conversation_id,
                text=text,
                metadata=metadata,
                memory_scope=memory_scope,
                context_key=context_key,
            )
        else:
            # Old sync interface (VectorMemoryStore)
            item_id = str(uuid.uuid4())
            # Prepare metadata with all context
            full_metadata = {
                "user_id": str(user_id),
                "conversation_id": str(conversation_id) if conversation_id else None,
                "memory_scope": memory_scope,
                "context_key": context_key,
                **metadata
            }
            # Call the synchronous add method
            self.vector_store.add(
                item_id=item_id,
                text=text,
                metadata=full_metadata,
            )
            return item_id

    async def store_structured(
        self,
        *,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID | None,
        kind: str,
        data: dict,
        memory_scope: str = "user",
        context_key: str | None = None,
    ) -> MemoryMetadata:
        row = MemoryMetadata(
            user_id=str(user_id),
            memory_scope=memory_scope,
            context_key=context_key,
            conversation_id=str(conversation_id) if conversation_id else None,
            kind=kind,
            data=data,
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def get_context_snapshot(
        self,
        *,
        user_id: uuid.UUID,
        memory_scope: str,
        context_key: str | None,
        query: str | None = None,
        top_k: int = 5,
        message_limit: int = 10,
        structured_limit: int = 10,
        conversation_id: uuid.UUID | None = None,
        exclude_kinds: list[str] | None = None,
    ) -> dict[str, Any]:
        uid_str = str(user_id)
        memories = []
        if query:
            memories = await self.vector_retrieve(
                user_id=user_id,
                query=query,
                top_k=top_k,
                memory_scope=memory_scope,
                context_key=context_key,
            )

        # Build structured query — exclude unwanted kinds at DB level
        where_clauses = [
            MemoryMetadata.user_id == uid_str,
            MemoryMetadata.memory_scope == memory_scope,
        ]
        # Fix: Use NOT IN with proper list instead of notin_ which breaks with context_key
        if exclude_kinds:
            # Filter out excluded kinds directly in Python after fetch for reliability
            pass  # We'll filter after the query

        structured_stmt = (
            select(MemoryMetadata)
            .where(*where_clauses)
            .order_by(desc(MemoryMetadata.created_at))
            .limit(structured_limit)
        )
        structured_result = await self.session.execute(structured_stmt)
        all_structured = list(structured_result.scalars().all())
        
        # Filter excluded kinds in Python for reliability
        if exclude_kinds:
            exclude_set = set(exclude_kinds)
            structured = [m for m in all_structured if m.kind not in exclude_set]
        else:
            structured = all_structured

        conversation_ids: list[str] = []
        if conversation_id:
            conversation_ids.append(str(conversation_id))
        else:
            conversation_stmt = (
                select(Conversation.id)
                .where(
                    Conversation.user_id == uid_str,
                    Conversation.memory_scope == memory_scope,
                    Conversation.context_key == context_key,
                )
                .order_by(desc(Conversation.created_at))
                .limit(10)
            )
            conversation_result = await self.session.execute(conversation_stmt)
            conversation_ids = [str(r) for r in conversation_result.scalars().all()]

        recent_messages: list[Message] = []
        if conversation_ids:
            message_stmt = (
                select(Message)
                .where(Message.conversation_id.in_(conversation_ids))
                .order_by(desc(Message.created_at))
                .limit(message_limit)
            )
            message_result = await self.session.execute(message_stmt)
            recent_messages = list(message_result.scalars().all())
            recent_messages.reverse()

        return {
            "memory_scope": memory_scope,
            "context_key": context_key,
            "recent_messages": recent_messages,
            "retrieved_memories": memories,
            "structured_memories": structured,
        }
