from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field


class PublicRunRequest(BaseModel):
    user_id: uuid.UUID
    input: str = Field(min_length=1)
    conversation_id: uuid.UUID | None = None
    provider: Literal["openai", "anthropic", "openrouter"] | None = None
    model: str | None = None
    memory_scope: Literal["conversation", "user", "workspace", "global"] = "workspace"
    context_key: str | None = Field(default="default", min_length=1, max_length=120)


class SkillInvokeRequest(PublicRunRequest):
    skill_arguments: str | None = Field(default=None, max_length=2000)


class PublicSkillSummary(BaseModel):
    name: str
    description: str
    invocation_mode: str
    tool_permissions: list[str] = Field(default_factory=list)
    when_to_use: str | None = None


class PublicRunResponse(BaseModel):
    conversation_id: uuid.UUID
    skill: str
    output: str
    provider: str | None = None
    model: str | None = None
    tool_calls: list[dict] = Field(default_factory=list)
    tool_results: list[dict] = Field(default_factory=list)
    metrics: dict | None = None


class PublicCompareRequest(PublicRunRequest):
    skill_name: str | None = Field(default=None, min_length=1, max_length=120)
    skill_arguments: str | None = Field(default=None, max_length=2000)


class UsageSummary(BaseModel):
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class CompareMetrics(BaseModel):
    latency_ms: int
    estimated_cost_usd: float = 0.0
    estimated_efficiency: int = 0
    estimated_accuracy: int = 0
    tool_count: int = 0
    memory_hits: int = 0
    usage: UsageSummary = Field(default_factory=UsageSummary)


class CompareSide(BaseModel):
    title: str
    provider: str | None = None
    model: str | None = None
    skill: str | None = None
    output: str
    tool_calls: list[dict] = Field(default_factory=list)
    tool_results: list[dict] = Field(default_factory=list)
    metrics: CompareMetrics
    error: str | None = None


class CompareDelta(BaseModel):
    latency_gap_ms: int
    token_gap: int = 0
    estimated_cost_gap_usd: float = 0.0
    tool_advantage: int = 0
    memory_advantage: int = 0
    efficiency_gap: int = 0
    accuracy_gap: int = 0


class PublicCompareResponse(BaseModel):
    conversation_id: uuid.UUID | None = None
    aurora_api_key: str | None = None
    baseline: CompareSide
    tuned: CompareSide
    delta: CompareDelta
