from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field

class MemoryRules(BaseModel):
    short_term: bool = True
    vector_store: bool = True
    structured: bool = True
    compose: list[str] = Field(default_factory=list)


class SkillCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(min_length=1, max_length=500)
    version: str = Field(default="1.0.0", max_length=32)
    triggers: list[str] = Field(default_factory=list)
    when_to_use: str | None = Field(default=None, max_length=1000)
    argument_hint: str | None = Field(default=None, max_length=200)
    prompt_template: str = Field(min_length=1)
    tool_permissions: list[str] = Field(default_factory=list)
    invocation_mode: Literal["auto", "manual", "hidden"] = "auto"
    context_mode: Literal["inline", "fork"] = "inline"
    preferred_model: str | None = None
    preferred_effort: Literal["low", "medium", "high", "xhigh", "max"] | None = None
    tool_rules: dict = Field(default_factory=dict)
    memory_rules: MemoryRules = Field(default_factory=MemoryRules)


class SkillResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    version: str
    triggers: list[str]
    when_to_use: str | None = None
    argument_hint: str | None = None
    prompt_template: str
    tool_permissions: list[str]
    memory_rules: dict
    is_builtin: bool = False
    invocation_mode: Literal["auto", "manual", "hidden"] = "auto"
    context_mode: Literal["inline", "fork"] = "inline"
    preferred_model: str | None = None
    preferred_effort: Literal["low", "medium", "high", "xhigh", "max"] | None = None
    tool_rules: dict = Field(default_factory=dict)


class SkillImportRequest(BaseModel):
    source: str = Field(min_length=1, description="Local directory path or git repository URL")
    mode: Literal["local", "git"] = "local"
    prefix: str | None = Field(default=None, max_length=40)
    invocation_mode: Literal["auto", "manual", "hidden"] | None = None
    overwrite: bool = False


class SkillImportResult(BaseModel):
    imported: list[str] = Field(default_factory=list)
    skipped: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
