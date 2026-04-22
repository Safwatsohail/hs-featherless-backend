from __future__ import annotations

from collections import Counter
from typing import Any
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import get_settings
from backend.app.db.session import get_db
from backend.app.models import ApiKey, Conversation, MemoryMetadata, Message, Skill
from backend.app.schemas.tool import (
    ExternalToolCreate,
    OverviewStats,
    ToolDescriptor,
    ToolRunRequest,
    ToolRunResponse,
    ToolStatsItem,
)
from backend.app.services.tool_engine import ToolEngine, ToolError

router = APIRouter(prefix="/tools", tags=["tools"])


@router.get("", response_model=list[ToolDescriptor])
async def list_tools(db: AsyncSession = Depends(get_db)) -> list[ToolDescriptor]:
    settings = get_settings()
    engine = ToolEngine(
        db=db,
        python_timeout_seconds=settings.python_tool_timeout_seconds,
        bash_timeout_seconds=settings.bash_tool_timeout_seconds,
        http_timeout_seconds=settings.http_tool_timeout_seconds,
        web_search_max_results=settings.web_search_max_results,
        deep_search_max_pages=settings.deep_search_max_pages,
    )
    return await engine.list_tools()


@router.post("/external", response_model=ToolDescriptor)
async def create_external_tool(
    payload: ExternalToolCreate, db: AsyncSession = Depends(get_db)
) -> ToolDescriptor:
    settings = get_settings()
    engine = ToolEngine(
        db=db,
        python_timeout_seconds=settings.python_tool_timeout_seconds,
        bash_timeout_seconds=settings.bash_tool_timeout_seconds,
        http_timeout_seconds=settings.http_tool_timeout_seconds,
        web_search_max_results=settings.web_search_max_results,
        deep_search_max_pages=settings.deep_search_max_pages,
    )
    created = await engine.create_external_tool(payload)
    return ToolDescriptor(
        name=created.name,
        description=created.description,
        input_schema=created.input_schema or {},
    )


@router.post("/run", response_model=ToolRunResponse)
async def run_tool(payload: ToolRunRequest, db: AsyncSession = Depends(get_db)) -> ToolRunResponse:
    settings = get_settings()
    engine = ToolEngine(
        db=db,
        python_timeout_seconds=settings.python_tool_timeout_seconds,
        bash_timeout_seconds=settings.bash_tool_timeout_seconds,
        http_timeout_seconds=settings.http_tool_timeout_seconds,
        web_search_max_results=settings.web_search_max_results,
        deep_search_max_pages=settings.deep_search_max_pages,
    )
    try:
        result = await engine.execute_tool(payload.name, payload.input)
    except ToolError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ToolRunResponse(name=result.name, output=result.output, metadata=result.metadata)


@router.get("/overview", response_model=OverviewStats)
async def overview_stats(
    user_id: uuid.UUID | None = Query(default=None),
    memory_scope: str | None = Query(default=None),
    context_key: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> OverviewStats:
    filters: list[Any] = []
    if user_id:
        filters.append(Conversation.user_id == user_id)
    if memory_scope:
        filters.append(Conversation.memory_scope == memory_scope)
    if context_key is not None:
        filters.append(Conversation.context_key == context_key)

    conversation_stmt = select(Conversation).order_by(desc(Conversation.created_at))
    message_stmt = select(Message)
    memory_stmt = select(MemoryMetadata)
    if filters:
        conversation_stmt = conversation_stmt.where(*filters)
        memory_filters: list[Any] = []
        if user_id:
            memory_filters.append(MemoryMetadata.user_id == user_id)
        if memory_scope:
            memory_filters.append(MemoryMetadata.memory_scope == memory_scope)
        if context_key is not None:
            memory_filters.append(MemoryMetadata.context_key == context_key)
        if memory_filters:
            memory_stmt = memory_stmt.where(*memory_filters)

    conversation_ids = select(Conversation.id)
    if filters:
        conversation_ids = conversation_ids.where(*filters)
        message_stmt = message_stmt.where(Message.conversation_id.in_(conversation_ids))
    elif user_id:
        message_stmt = message_stmt.where(Message.user_id == user_id)

    conversations = list((await db.execute(conversation_stmt.limit(8))).scalars().all())
    messages = list((await db.execute(message_stmt)).scalars().all())
    memories = list((await db.execute(memory_stmt)).scalars().all())
    skills_count = (await db.execute(select(func.count()).select_from(Skill))).scalar_one()
    api_key_count = (await db.execute(select(func.count()).select_from(ApiKey))).scalar_one()
    conversations_total = (
        await db.execute(select(func.count()).select_from(Conversation).where(*filters))
        if filters
        else await db.execute(select(func.count()).select_from(Conversation))
    ).scalar_one()
    messages_total = (
        await db.execute(select(func.count()).select_from(message_stmt.subquery()))
    ).scalar_one()
    memory_total = (
        await db.execute(select(func.count()).select_from(memory_stmt.subquery()))
    ).scalar_one()
    settings = get_settings()
    tools_total = len(
        await ToolEngine(
            db=db,
            python_timeout_seconds=settings.python_tool_timeout_seconds,
            bash_timeout_seconds=settings.bash_tool_timeout_seconds,
            http_timeout_seconds=settings.http_tool_timeout_seconds,
            web_search_max_results=settings.web_search_max_results,
            deep_search_max_pages=settings.deep_search_max_pages,
        ).list_tools()
    )

    skill_counter: Counter[str] = Counter()
    tool_counter: Counter[str] = Counter()
    for row in memories:
        data = row.data or {}
        if row.kind == "turn" and isinstance(data.get("skill"), str):
            skill_counter[str(data["skill"])] += 1
        if row.kind == "tool_calls":
            for item in data.get("tool_calls", []):
                name = str((item or {}).get("name") or "").strip()
                if name:
                    tool_counter[name] += 1

    recent_conversations: list[dict] = []
    for conversation in conversations:
        recent_conversations.append(
            {
                "id": str(conversation.id),
                "title": conversation.title,
                "memory_scope": conversation.memory_scope,
                "context_key": conversation.context_key,
                "created_at": conversation.created_at.isoformat(),
            }
        )

    return OverviewStats(
        totals={
            "conversations": int(conversations_total or 0),
            "messages": int(messages_total or 0),
            "memory_rows": int(memory_total or 0),
            "skills": int(skills_count or 0),
            "api_keys": int(api_key_count or 0),
            "tools": tools_total,
        },
        skill_usage=[ToolStatsItem(name=name, count=count) for name, count in skill_counter.most_common(10)],
        tool_usage=[ToolStatsItem(name=name, count=count) for name, count in tool_counter.most_common(10)],
        recent_conversations=recent_conversations,
    )
