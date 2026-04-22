from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import get_settings
from backend.app.db.session import get_db
from backend.app.schemas.chat import ChatRequest, ChatResponse
from backend.app.services.api_key_service import ApiKeyService
from backend.app.services.llm_client import LLMError
from backend.app.services.memory_engine import MemoryEngine
from backend.app.services.orchestrator import Orchestrator
from backend.app.services.skill_engine import SkillEngine
from backend.app.services.tool_engine import ToolError
from backend.app.services.tool_engine import ToolEngine

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request, db: AsyncSession = Depends(get_db)) -> ChatResponse:
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

    orch = Orchestrator(
        db=db,
        api_keys=api_keys,
        skills=skills,
        memory=memory,
        tools=tools,
        llm_base_urls={
            "openai": settings.openai_base_url,
            "anthropic": settings.anthropic_base_url,
            "openrouter": settings.openrouter_base_url,
        },
        default_provider=settings.default_llm_provider,
        default_model=settings.default_llm_model,
        vector_top_k=settings.vector_top_k,
    )
    db.info["decision_llm_provider"] = settings.decision_llm_provider
    db.info["decision_llm_model"] = settings.decision_llm_model
    try:
        res = await orch.process_request(
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
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ToolError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return ChatResponse(
        conversation_id=res.conversation_id,
        skill=res.skill,
        tool_calls=res.tool_calls,
        tool_results=res.tool_results,
        provider=res.provider,
        model=res.model,
        output=res.output,
    )
