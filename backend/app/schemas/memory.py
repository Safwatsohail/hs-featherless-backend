from __future__ import annotations

import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field


class MemoryStoreRequest(BaseModel):
    user_id: uuid.UUID
    conversation_id: uuid.UUID | None = None
    text: str = Field(min_length=1)
    kind: str = Field(default="note", min_length=1)
    memory_scope: Literal["conversation", "user", "workspace", "global"] = "user"
    context_key: str | None = Field(default=None, min_length=1, max_length=120)
    metadata: dict[str, Any] = Field(default_factory=dict)

class MemoryHit(BaseModel):
    id: str
    text: str
    score: float
    metadata: dict[str, Any] = Field(default_factory=dict)

class MemoryRetrieveResponse(BaseModel):
    hits: list[MemoryHit]


class ContextMemoryRequest(BaseModel):
    user_id: uuid.UUID
    conversation_id: uuid.UUID | None = None
    query: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)
    message_limit: int = Field(default=10, ge=1, le=50)
    structured_limit: int = Field(default=10, ge=1, le=50)
    memory_scope: Literal["conversation", "user", "workspace", "global"] = "user"
    context_key: str | None = Field(default=None, min_length=1, max_length=120)


class ContextMessage(BaseModel):
    role: str
    content: str
    created_at: str


class StructuredMemoryItem(BaseModel):
    id: str
    kind: str
    data: dict[str, Any]
    created_at: str


class ContextMemoryResponse(BaseModel):
    memory_scope: str
    context_key: str | None = None
    recent_messages: list[ContextMessage]
    retrieved_memories: list[MemoryHit]
    structured_memories: list[StructuredMemoryItem]
