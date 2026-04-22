from __future__ import annotations

import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field


class CompareRequest(BaseModel):
    user_id: uuid.UUID
    input: str = Field(min_length=1)
    provider: Literal["openai", "anthropic", "openrouter"] | None = None
    model: str | None = None
    memory_scope: Literal["conversation", "user", "workspace", "global"] = "workspace"
    context_key: str | None = Field(default="default", min_length=1, max_length=120)
    skill_name: str | None = Field(default=None, min_length=1, max_length=80)
    tool_mode: str | None = Field(default=None, max_length=80)
    conversation_id: uuid.UUID | None = None


class CompareStats(BaseModel):
    latency_ms: int
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    estimated_credit_units: float | None = None
    tool_count: int = 0
    memory_hits: int | None = None
    quality_estimate: int | None = None


class CompareSide(BaseModel):
    label: str
    output: str
    provider: str | None = None
    model: str | None = None
    stats: CompareStats
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    tool_results: list[dict[str, Any]] = Field(default_factory=list)


class CompareResponse(BaseModel):
    aurora_api_key: str | None = None
    conversation_id: uuid.UUID | None = None
    tuned: CompareSide
    raw: CompareSide
