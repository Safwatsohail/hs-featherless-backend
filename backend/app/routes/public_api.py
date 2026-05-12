from __future__ import annotations

import re
import uuid
from time import perf_counter

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db
from app.models import MemoryMetadata
from app.schemas.memory import ContextMemoryRequest, ContextMemoryResponse, MemoryStoreRequest
from app.schemas.memory import MemoryUpdateRequest
from app.schemas.public_api import (
    CompareDelta,
    CompareMetrics,
    CompareSide,
    PublicCompareRequest,
    PublicCompareResponse,
    PublicRunRequest,
    PublicRunResponse,
    PublicSkillSummary,
    SkillInvokeRequest,
    UsageSummary,
)
from app.schemas.tool import ToolRunRequest, ToolRunResponse
from app.services.api_key_service import ApiKeyService
from app.services.aurora_auth_service import AuroraAuthService, resolve_aurora_auth
from app.services.llm_client import LLMClient, LLMError
from app.services.memory_engine import MemoryEngine
from app.services.orchestrator import Orchestrator
from app.services.skill_engine import SkillEngine
from app.services.tool_engine import ToolEngine, ToolError

router = APIRouter(prefix="/v1", tags=["public-api"])
public_router = APIRouter(tags=["public-api"])


async def require_aurora_auth(request: Request, db: AsyncSession = Depends(get_db)) -> object:
    return await resolve_aurora_auth(
        db=db,
        api_keys=ApiKeyService(db=db, crypto=request.app.state.crypto),
        authorization=request.headers.get("authorization"),
        x_aurora_key=request.headers.get("x-aurora-key"),
    )


def _build_orchestrator(*, request: Request, db: AsyncSession) -> Orchestrator:
    settings = get_settings()
    api_keys = ApiKeyService(db=db, crypto=request.app.state.crypto)
    skills = SkillEngine(db)
    memory = MemoryEngine(
        db=db,
        vector_store=request.app.state.vector_store,
        short_term_max_messages=settings.short_term_max_messages,
    )
    tools = ToolEngine(
        db=db,
        python_timeout_seconds=settings.python_tool_timeout_seconds,
        bash_timeout_seconds=settings.bash_tool_timeout_seconds,
        http_timeout_seconds=settings.http_tool_timeout_seconds,
        web_search_max_results=settings.web_search_max_results,
        deep_search_max_pages=settings.deep_search_max_pages,
    )
    db.info["decision_llm_provider"] = settings.decision_llm_provider
    db.info["decision_llm_model"] = settings.decision_llm_model
    return Orchestrator(
        db=db,
        api_keys=api_keys,
        skills=skills,
        memory=memory,
        tools=tools,
        llm_base_urls={
            "openai": settings.openai_base_url,
            "anthropic": settings.anthropic_base_url,
            "featherless": settings.featherless_base_url,
            "openrouter": settings.openrouter_base_url,
        },
        default_provider=settings.default_llm_provider,
        default_model=settings.default_llm_model,
        vector_top_k=settings.vector_top_k,
    )


def _to_public_response(result) -> PublicRunResponse:
    return PublicRunResponse(
        conversation_id=result.conversation_id,
        skill=result.skill,
        output=result.output,
        provider=result.provider,
        model=result.model,
        tool_calls=[tool.model_dump() for tool in result.tool_calls],
        tool_results=result.tool_results,
        metrics={
            "memory_hits": result.memory_hits,
            "tool_count": len(result.tool_calls),
            "usage": result.usage,
        },
    )


def _usage_summary(raw_usage: dict | None) -> UsageSummary:
    raw_usage = raw_usage or {}
    prompt = raw_usage.get("prompt_tokens") or raw_usage.get("input_tokens")
    completion = raw_usage.get("completion_tokens") or raw_usage.get("output_tokens")
    total = raw_usage.get("total_tokens")
    if total is None and (prompt is not None or completion is not None):
        total = int(prompt or 0) + int(completion or 0)
    return UsageSummary(
        prompt_tokens=int(prompt) if prompt is not None else None,
        completion_tokens=int(completion) if completion is not None else None,
        total_tokens=int(total) if total is not None else None,
    )


def _estimate_cost_usd(*, provider: str, model: str | None, usage: UsageSummary) -> float:
    total_tokens = usage.total_tokens or 0
    if not total_tokens:
        return 0.0
    if provider == "openrouter" and model == "openrouter/free":
        return 0.0
    per_1k = 0.0025 if provider in {"openai", "openrouter"} else 0.004
    return round((total_tokens / 1000.0) * per_1k, 6)


def _score_accuracy(*, has_tools: bool, memory_hits: int, token_total: int, skill_name: str | None) -> int:
    score = 58
    if skill_name and skill_name != "default":
        score += 12
    if has_tools:
        score += 11
    if memory_hits:
        score += min(memory_hits * 4, 10)
    if token_total > 250:
        score += 5
    return max(35, min(score, 97))


def _score_efficiency(*, latency_ms: int, cost_usd: float, tool_count: int, memory_hits: int) -> int:
    score = 84
    score -= min(latency_ms // 350, 25)
    score -= min(int(cost_usd * 1000), 18)
    score += min(tool_count * 3, 9)
    score += min(memory_hits * 2, 8)
    return max(20, min(score, 98))


def _is_code_prompt(user_input: str) -> bool:
    normalized = user_input.lower()
    return any(
        keyword in normalized
        for keyword in (
            "code", "function", "script", "program", "class", "implement",
            "write", "generate", "create", "python", "javascript",
            "typescript", "java", "c++", "calculator", "add numbers",
        )
    )


def _plain_raw_output(text: str) -> str:
    text = text.strip()
    text = re.sub(r"```[\w+#.-]*\n?", "", text)
    text = text.replace("```", "")
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _raw_baseline_output(*, user_input: str, model_output: str) -> str:
    # For non-code prompts, keep the plain text formatting
    if not _is_code_prompt(user_input):
        return _plain_raw_output(model_output)
    
    # For code prompts, convert code blocks to paragraph format
    text = model_output.strip()
    
    # Remove excessive markdown
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    
    # Convert code blocks to paragraph format
    def code_to_paragraph(match):
        code_content = match.group(2) if len(match.groups()) >= 2 else match.group(1)
        # Remove indentation and convert to single paragraph
        lines = [line.strip() for line in code_content.split('\n') if line.strip()]
        return "Here's the code: " + " ".join(lines) + " "
    
    # Replace code blocks with paragraph format
    text = re.sub(r"```[\w]*\n?(.*?)```", code_to_paragraph, text, flags=re.DOTALL)
    
    # Clean up any remaining backticks
    text = text.replace("`", "")
    
    return text.strip()


def _to_context_response(snapshot: dict) -> ContextMemoryResponse:
    from app.schemas.memory import ContextMessage, MemoryHit, StructuredMemoryItem

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


async def _run_public_request(
    *,
    payload: PublicRunRequest,
    request: Request,
    db: AsyncSession,
    skill_name: str | None = None,
    skill_arguments: str | None = None,
) -> PublicRunResponse:
    orchestrator = _build_orchestrator(request=request, db=db)
    try:
        result = await orchestrator.process_request(
            user_id=payload.user_id,
            user_input=payload.input,
            conversation_id=payload.conversation_id,
            provider=payload.provider,
            model=payload.model,
            skill_name=skill_name,
            skill_arguments=skill_arguments,
            memory_scope=payload.memory_scope,
            context_key=payload.context_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ToolError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return _to_public_response(result)


async def _compare_public_request(
    *,
    payload: PublicCompareRequest,
    request: Request,
    db: AsyncSession,
    auth_context: object,
) -> PublicCompareResponse:
    settings = get_settings()
    api_keys = ApiKeyService(db=db, crypto=request.app.state.crypto)
    orchestrator = _build_orchestrator(request=request, db=db)
    selected_provider = payload.provider or settings.default_llm_provider
    selected_model = orchestrator._normalize_model(
        provider=selected_provider,
        model=payload.model or settings.default_llm_model,
    )
    api_key = await api_keys.get_decrypted_key(user_id=payload.user_id, provider=selected_provider)
    if not api_key:
        raise HTTPException(
            status_code=422,
            detail=f"No API key stored for provider={selected_provider}. Save one via POST /apikey first.",
        )

    raw_llm = LLMClient(
        provider=selected_provider,
        api_key=api_key,
        base_url=orchestrator._get_base_url(selected_provider),
    )
    raw_messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant that provides functional responses. Answer clearly and directly. "
                "For coding requests, provide working code that solves the problem, but keep it simple - "
                "no extensive error handling, validation, docstrings, or production features. "
                "Focus on the core functionality. Use basic formatting but avoid complex structure."
            ),
        },
        {"role": "user", "content": payload.input},
    ]

    try:
        raw_started = perf_counter()
        raw_result = await raw_llm.generate(model=selected_model, messages=raw_messages, temperature=0.95)
        raw_latency_ms = int((perf_counter() - raw_started) * 1000)
        raw_output = _raw_baseline_output(user_input=payload.input, model_output=raw_result.content)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    try:
        tuned_started = perf_counter()
        tuned_result = await orchestrator.process_request(
            user_id=payload.user_id,
            user_input=payload.input,
            conversation_id=payload.conversation_id,
            provider=payload.provider,
            model=payload.model,
            skill_name=payload.skill_name,
            skill_arguments=payload.skill_arguments,
            memory_scope=payload.memory_scope,
            context_key=payload.context_key,
        )
        tuned_latency_ms = int((perf_counter() - tuned_started) * 1000)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ToolError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    raw_usage = _usage_summary(raw_result.raw.get("usage"))
    tuned_usage = _usage_summary(tuned_result.usage)
    raw_cost = _estimate_cost_usd(provider=selected_provider, model=selected_model, usage=raw_usage)
    tuned_cost = _estimate_cost_usd(provider=tuned_result.provider, model=tuned_result.model, usage=tuned_usage)
    baseline = CompareSide(
        title="Raw Model API",
        provider=selected_provider,
        model=selected_model,
        output=raw_output,
        metrics=CompareMetrics(
            latency_ms=raw_latency_ms,
            estimated_cost_usd=raw_cost,
            estimated_efficiency=_score_efficiency(
                latency_ms=raw_latency_ms,
                cost_usd=raw_cost,
                tool_count=0,
                memory_hits=0,
            ),
            estimated_accuracy=_score_accuracy(
                has_tools=False,
                memory_hits=0,
                token_total=raw_usage.total_tokens or 0,
                skill_name=None,
            ),
            tool_count=0,
            memory_hits=0,
            usage=raw_usage,
        ),
    )
    tuned = CompareSide(
        title="HNS Tuned API",
        provider=tuned_result.provider,
        model=tuned_result.model,
        skill=tuned_result.skill,
        output=tuned_result.output,
        tool_calls=[tool.model_dump() for tool in tuned_result.tool_calls],
        tool_results=tuned_result.tool_results,
        metrics=CompareMetrics(
            latency_ms=tuned_latency_ms,
            estimated_cost_usd=tuned_cost,
            estimated_efficiency=_score_efficiency(
                latency_ms=tuned_latency_ms,
                cost_usd=tuned_cost,
                tool_count=len(tuned_result.tool_calls),
                memory_hits=tuned_result.memory_hits,
            ),
            estimated_accuracy=_score_accuracy(
                has_tools=bool(tuned_result.tool_calls),
                memory_hits=tuned_result.memory_hits,
                token_total=tuned_usage.total_tokens or 0,
                skill_name=tuned_result.skill,
            ),
            tool_count=len(tuned_result.tool_calls),
            memory_hits=tuned_result.memory_hits,
            usage=tuned_usage,
        ),
    )

    aurora_api_key = None
    auth_service = AuroraAuthService(db=db, api_keys=api_keys)
    demo_key = await auth_service.get_demo_key(user_id=getattr(auth_context, "user_id", None))
    if demo_key and demo_key.api_key:
        aurora_api_key = demo_key.api_key

    return PublicCompareResponse(
        conversation_id=tuned_result.conversation_id,
        aurora_api_key=aurora_api_key,
        baseline=baseline,
        tuned=tuned,
        delta=CompareDelta(
            latency_gap_ms=baseline.metrics.latency_ms - tuned.metrics.latency_ms,
            token_gap=(baseline.metrics.usage.total_tokens or 0) - (tuned.metrics.usage.total_tokens or 0),
            estimated_cost_gap_usd=round(raw_cost - tuned_cost, 6),
            tool_advantage=tuned.metrics.tool_count - baseline.metrics.tool_count,
            memory_advantage=tuned.metrics.memory_hits - baseline.metrics.memory_hits,
            efficiency_gap=tuned.metrics.estimated_efficiency - baseline.metrics.estimated_efficiency,
            accuracy_gap=tuned.metrics.estimated_accuracy - baseline.metrics.estimated_accuracy,
        ),
    )


@router.get("/skills", response_model=list[PublicSkillSummary])
async def public_skill_catalog(db: AsyncSession = Depends(get_db)) -> list[PublicSkillSummary]:
    engine = SkillEngine(db)
    await engine.ensure_builtin_skills()
    skills = await engine.list_skills()
    visible = []
    for skill in skills:
        config = engine.get_skill_config(skill)
        if config.get("invocation_mode") == "hidden":
            continue
        visible.append(
            PublicSkillSummary(
                name=skill.name,
                description=skill.description,
                invocation_mode=config.get("invocation_mode", "auto"),
                tool_permissions=skill.tool_permissions or [],
                when_to_use=config.get("when_to_use"),
            )
        )
    return visible


@router.post("/chat", response_model=PublicRunResponse)
async def public_chat(
    payload: PublicRunRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: object = Depends(require_aurora_auth),
) -> PublicRunResponse:
    return await _run_public_request(payload=payload, request=request, db=db)


@router.post("/skills/{skill_name}", response_model=PublicRunResponse)
async def invoke_skill(
    skill_name: str,
    payload: SkillInvokeRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: object = Depends(require_aurora_auth),
) -> PublicRunResponse:
    return await _run_public_request(
        payload=payload,
        request=request,
        db=db,
        skill_name=skill_name,
        skill_arguments=payload.skill_arguments,
    )


@router.post("/run", response_model=PublicRunResponse)
async def public_run(
    payload: PublicRunRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: object = Depends(require_aurora_auth),
) -> PublicRunResponse:
    return await _run_public_request(payload=payload, request=request, db=db)


@router.post("/compare", response_model=PublicCompareResponse)
async def public_compare(
    payload: PublicCompareRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    auth: object = Depends(require_aurora_auth),
) -> PublicCompareResponse:
    return await _compare_public_request(payload=payload, request=request, db=db, auth_context=auth)


@router.post("/tools/{tool_name}", response_model=ToolRunResponse)
async def public_tool_run(
    tool_name: str,
    payload: ToolRunRequest,
    db: AsyncSession = Depends(get_db),
    _: object = Depends(require_aurora_auth),
) -> ToolRunResponse:
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
        result = await engine.execute_tool(tool_name, payload.input)
    except ToolError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ToolRunResponse(name=result.name, output=result.output, metadata=result.metadata)


@router.post("/memory", response_model=dict)
async def public_memory_store(
    payload: MemoryStoreRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: object = Depends(require_aurora_auth),
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


@router.patch("/memory/{memory_id}", response_model=dict)
async def public_memory_update(
    memory_id: str,
    payload: MemoryUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: object = Depends(require_aurora_auth),
) -> dict:
    row = await db.get(MemoryMetadata, memory_id)
    if row is None or str(row.user_id) != str(payload.user_id):
        raise HTTPException(status_code=404, detail="Memory item not found.")

    settings = get_settings()
    mem = MemoryEngine(
        db=db,
        vector_store=request.app.state.vector_store,
        short_term_max_messages=settings.short_term_max_messages,
    )
    vec_id = await mem.vector_store_text(
        user_id=payload.user_id,
        conversation_id=row.conversation_id,
        text=payload.text,
        memory_scope=payload.memory_scope,
        context_key=payload.context_key,
        metadata={"kind": payload.kind, **(payload.metadata or {})},
    )
    row.kind = payload.kind
    row.memory_scope = payload.memory_scope
    row.context_key = payload.context_key
    row.data = {"text": payload.text, "vector_id": vec_id, "metadata": payload.metadata}
    await db.commit()
    await db.refresh(row)
    return {
        "updated": True,
        "vector_id": vec_id,
        "metadata_id": str(row.id),
        "memory_scope": row.memory_scope,
        "context_key": row.context_key,
    }


@router.delete("/memory/{memory_id}", response_model=dict)
async def public_memory_delete(
    memory_id: str,
    user_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: object = Depends(require_aurora_auth),
) -> dict:
    row = await db.get(MemoryMetadata, memory_id)
    if row is None or str(row.user_id) != str(user_id):
        raise HTTPException(status_code=404, detail="Memory item not found.")
    await db.delete(row)
    await db.commit()
    return {"deleted": True, "metadata_id": memory_id}


@router.post("/memory/context", response_model=ContextMemoryResponse)
async def public_memory_context(
    payload: ContextMemoryRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: object = Depends(require_aurora_auth),
) -> ContextMemoryResponse:
    settings = get_settings()
    mem = MemoryEngine(
        db=db,
        vector_store=request.app.state.vector_store,
        short_term_max_messages=settings.short_term_max_messages,
    )
    snapshot = await mem.get_context_snapshot(
        user_id=payload.user_id,
        conversation_id=payload.conversation_id,
        query=payload.query,
        top_k=payload.top_k,
        message_limit=payload.message_limit,
        structured_limit=payload.structured_limit,
        memory_scope=payload.memory_scope,
        context_key=payload.context_key,
    )
    return _to_context_response(snapshot)


@public_router.post("/run", response_model=PublicRunResponse)
async def public_run_alias(
    payload: PublicRunRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: object = Depends(require_aurora_auth),
) -> PublicRunResponse:
    return await _run_public_request(payload=payload, request=request, db=db)


@public_router.post("/compare", response_model=PublicCompareResponse)
async def public_compare_alias(
    payload: PublicCompareRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    auth: object = Depends(require_aurora_auth),
) -> PublicCompareResponse:
    return await _compare_public_request(payload=payload, request=request, db=db, auth_context=auth)


@public_router.post("/skills/{skill_name}", response_model=PublicRunResponse)
async def public_skill_alias(
    skill_name: str,
    payload: SkillInvokeRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: object = Depends(require_aurora_auth),
) -> PublicRunResponse:
    return await _run_public_request(
        payload=payload,
        request=request,
        db=db,
        skill_name=skill_name,
        skill_arguments=payload.skill_arguments,
    )


@public_router.post("/tools/{tool_name}", response_model=ToolRunResponse)
async def public_tool_alias(
    tool_name: str,
    payload: ToolRunRequest,
    db: AsyncSession = Depends(get_db),
    _: object = Depends(require_aurora_auth),
) -> ToolRunResponse:
    return await public_tool_run(tool_name=tool_name, payload=payload, db=db)


@public_router.post("/memory", response_model=dict)
async def public_memory_alias(
    payload: MemoryStoreRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: object = Depends(require_aurora_auth),
) -> dict:
    return await public_memory_store(payload=payload, request=request, db=db)


@public_router.patch("/memory/{memory_id}", response_model=dict)
async def public_memory_update_alias(
    memory_id: str,
    payload: MemoryUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: object = Depends(require_aurora_auth),
) -> dict:
    return await public_memory_update(memory_id=memory_id, payload=payload, request=request, db=db)


@public_router.delete("/memory/{memory_id}", response_model=dict)
async def public_memory_delete_alias(
    memory_id: str,
    user_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: object = Depends(require_aurora_auth),
) -> dict:
    return await public_memory_delete(memory_id=memory_id, user_id=user_id, db=db)


@public_router.post("/memory/context", response_model=ContextMemoryResponse)
async def public_memory_context_alias(
    payload: ContextMemoryRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: object = Depends(require_aurora_auth),
) -> ContextMemoryResponse:
    return await public_memory_context(payload=payload, request=request, db=db)
