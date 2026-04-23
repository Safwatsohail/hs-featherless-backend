"""
Streaming API with Server-Sent Events for real-time LLM responses.
Provides tool execution visibility and skill routing transparency.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import get_settings
from backend.app.db.session import get_db
from backend.app.schemas.chat import ChatRequest
from backend.app.services.api_key_service import ApiKeyService
from backend.app.services.llm_client import LLMError
from backend.app.services.memory_engine import MemoryEngine
from backend.app.services.orchestrator import Orchestrator
from backend.app.services.skill_engine import SkillEngine
from backend.app.services.tool_engine import ToolEngine, ToolError

router = APIRouter(tags=["streaming"])


async def stream_chat_response(
    payload: ChatRequest,
    request: Request,
    db: AsyncSession,
) -> AsyncGenerator[str, None]:
    """Stream chat response with SSE format."""
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
        http_timeout_seconds=settings.http_timeout_seconds,
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
            "featherless": settings.featherless_base_url,
            "openrouter": settings.openrouter_base_url,
        },
        default_provider=settings.default_llm_provider,
        default_model=settings.default_llm_model,
        vector_top_k=settings.vector_top_k,
    )
    db.info["decision_llm_provider"] = settings.decision_llm_provider
    db.info["decision_llm_model"] = settings.decision_llm_model
    
    try:
        # Send initial event
        yield f"event: start\ndata: {json.dumps({'request_id': str(uuid.uuid4())})}\n\n"
        
        # Skill selection phase
        yield f"event: skill_selection\ndata: {json.dumps({'status': 'selecting'})}\n\n"
        await asyncio.sleep(0.1)  # Allow client to process
        
        # Process request with streaming updates
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
        
        # Send skill selected event
        yield f"event: skill_selected\ndata: {json.dumps({'skill': res.skill})}\n\n"
        
        # Send tool execution events
        if res.tool_calls:
            for i, tool_call in enumerate(res.tool_calls):
                yield f"event: tool_start\ndata: {json.dumps({'tool': tool_call.name, 'input': tool_call.input})}\n\n"
                await asyncio.sleep(0.05)
                
                if i < len(res.tool_results):
                    tool_result = res.tool_results[i]
                    yield f"event: tool_complete\ndata: {json.dumps({'tool': tool_result['name'], 'output_preview': str(tool_result['output'])[:200]})}\n\n"
        
        # Send memory context event
        yield f"event: memory\ndata: {json.dumps({'hits': res.memory_hits, 'messages': res.short_context_messages})}\n\n"
        
        # Stream the final response in chunks
        output_chunks = [res.output[i:i+100] for i in range(0, len(res.output), 100)]
        for chunk in output_chunks:
            yield f"event: content\ndata: {json.dumps({'chunk': chunk})}\n\n"
            await asyncio.sleep(0.02)  # Simulate streaming
        
        # Send completion event
        yield f"event: done\ndata: {json.dumps({'conversation_id': str(res.conversation_id), 'provider': res.provider, 'model': res.model, 'usage': res.usage})}\n\n"
        
    except ValueError as exc:
        yield f"event: error\ndata: {json.dumps({'error': str(exc), 'type': 'validation'})}\n\n"
    except ToolError as exc:
        yield f"event: error\ndata: {json.dumps({'error': str(exc), 'type': 'tool'})}\n\n"
    except LLMError as exc:
        yield f"event: error\ndata: {json.dumps({'error': str(exc), 'type': 'llm'})}\n\n"
    except Exception as exc:
        yield f"event: error\ndata: {json.dumps({'error': str(exc), 'type': 'internal'})}\n\n"


@router.post("/stream/chat")
async def stream_chat(
    payload: ChatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    Stream chat responses with Server-Sent Events.
    
    Events:
    - start: Request initiated
    - skill_selection: Skill routing in progress
    - skill_selected: Skill chosen
    - tool_start: Tool execution started
    - tool_complete: Tool execution finished
    - memory: Memory context loaded
    - content: Response content chunk
    - done: Request completed
    - error: Error occurred
    """
    return StreamingResponse(
        stream_chat_response(payload, request, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
