from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.memory import (
    ContextMemoryResponse,
    ContextMessage,
    MemoryHit,
    MemoryRetrieveResponse,
    MemoryStoreRequest,
    StructuredMemoryItem,
)
from app.services.memory_engine import MemoryEngine

router = APIRouter(prefix="/memory", tags=["memory"])


@router.post("")
async def store_memory(
    payload: MemoryStoreRequest, request: Request, db: AsyncSession = Depends(get_db)
) -> dict:
    settings = get_settings()
    mem = MemoryEngine(
        db=db,
        vector_store=request.app.state.vector_store,
        short_term_max_messages=settings.short_term_max_messages,
    )
    vec_id = await mem.vector_store_text(
        user_id=payload.user_id,
        conversation_id=payload.conversation_id,
        text=payload.text,
        memory_scope=payload.memory_scope,
        context_key=payload.context_key,
        metadata={"kind": payload.kind, **(payload.metadata or {})},
    )
    row = await mem.store_structured(
        user_id=payload.user_id,
        conversation_id=payload.conversation_id,
        kind=payload.kind,
        memory_scope=payload.memory_scope,
        context_key=payload.context_key,
        data={"text": payload.text, "vector_id": vec_id, "metadata": payload.metadata},
    )
    return {
        "stored": True,
        "vector_id": vec_id,
        "metadata_id": str(row.id),
        "memory_scope": payload.memory_scope,
        "context_key": payload.context_key,
    }


@router.get("", response_model=MemoryRetrieveResponse)
async def retrieve_memory(
    request: Request,
    user_id: uuid.UUID = Query(...),
    query: str = Query(..., min_length=1),
    top_k: int = Query(3, ge=1, le=20),
    memory_scope: str = Query("user"),
    context_key: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> MemoryRetrieveResponse:
    settings = get_settings()
    mem = MemoryEngine(
        db=db,
        vector_store=request.app.state.vector_store,
        short_term_max_messages=settings.short_term_max_messages,
    )
    hits = await mem.vector_retrieve(
        user_id=user_id,
        query=query,
        top_k=top_k,
        memory_scope=memory_scope,
        context_key=context_key,
    )
    return MemoryRetrieveResponse(
        hits=[
            MemoryHit(
                id=str(h.get("id") or ""),
                text=str(h.get("text") or ""),
                score=float(h.get("score") or 0.0),
                metadata=h.get("metadata") or {},
            )
            for h in hits
        ]
    )


@router.get("/context", response_model=ContextMemoryResponse)
async def retrieve_context_memory(
    request: Request,
    user_id: uuid.UUID = Query(...),
    conversation_id: uuid.UUID | None = Query(default=None),
    query: str | None = Query(default=None),
    top_k: int = Query(5, ge=1, le=20),
    message_limit: int = Query(10, ge=1, le=50),
    structured_limit: int = Query(10, ge=1, le=50),
    memory_scope: str = Query("user"),
    context_key: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> ContextMemoryResponse:
    settings = get_settings()
    mem = MemoryEngine(
        db=db,
        vector_store=request.app.state.vector_store,
        short_term_max_messages=settings.short_term_max_messages,
    )
    snapshot = await mem.get_context_snapshot(
        user_id=user_id,
        conversation_id=conversation_id,
        query=query,
        top_k=top_k,
        message_limit=message_limit,
        structured_limit=structured_limit,
        memory_scope=memory_scope,
        context_key=context_key,
    )
    return ContextMemoryResponse(
        memory_scope=snapshot["memory_scope"],
        context_key=snapshot["context_key"],
        recent_messages=[
            ContextMessage(
                role=message.role,
                content=message.content,
                created_at=message.created_at.isoformat(),
            )
            for message in snapshot["recent_messages"]
        ],
        retrieved_memories=[
            MemoryHit(
                id=str(item.get("id") or ""),
                text=str(item.get("text") or ""),
                score=float(item.get("score") or 0.0),
                metadata=item.get("metadata") or {},
            )
            for item in snapshot["retrieved_memories"]
        ],
        structured_memories=[
            StructuredMemoryItem(
                id=str(item.id),
                kind=item.kind,
                data=item.data,
                created_at=item.created_at.isoformat(),
            )
            for item in snapshot["structured_memories"]
        ],
    )
