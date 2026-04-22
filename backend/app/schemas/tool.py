from __future__ import annotations

from pydantic import BaseModel, Field


class ToolDescriptor(BaseModel):
    name: str
    description: str
    input_schema: dict = Field(default_factory=dict)


class ExternalToolCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=500)
    endpoint_url: str = Field(min_length=1)
    method: str = Field(default="POST", pattern="^(GET|POST)$")
    headers: dict = Field(default_factory=dict)
    input_schema: dict = Field(default_factory=dict)


class ToolRunRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    input: dict = Field(default_factory=dict)


class ToolRunResponse(BaseModel):
    name: str
    output: str
    metadata: dict = Field(default_factory=dict)


class ToolStatsItem(BaseModel):
    name: str
    count: int


class OverviewStats(BaseModel):
    totals: dict
    skill_usage: list[ToolStatsItem] = Field(default_factory=list)
    tool_usage: list[ToolStatsItem] = Field(default_factory=list)
    recent_conversations: list[dict] = Field(default_factory=list)
