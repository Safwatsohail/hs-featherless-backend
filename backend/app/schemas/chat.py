from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: uuid.UUID
    conversation_id: uuid.UUID | None = None
    input: str = Field(min_length=1)
    provider: Literal["openai", "anthropic", "openrouter"] | None = None
    model: str | None = None
    skill_name: str | None = Field(default=None, min_length=1, max_length=80)
    skill_arguments: str | None = Field(default=None, max_length=2000)
    memory_scope: Literal["conversation", "user", "workspace", "global"] = "user"
    context_key: str | None = Field(default=None, min_length=1, max_length=120)


class ToolCall(BaseModel):
    name: str
    input: dict = Field(default_factory=dict)


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    skill: str
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tool_results: list[dict] = Field(default_factory=list)
    provider: str | None = None
    model: str | None = None
    output: str
