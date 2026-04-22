from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class AuroraKeyIssueRequest(BaseModel):
    user_id: uuid.UUID
    name: str = Field(default="default", min_length=1, max_length=120)
    scopes: list[str] = Field(default_factory=lambda: ["run", "skills", "tools", "memory"])


class AuroraKeyResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    key_prefix: str
    scopes: list[str]
    is_active: bool = True
    api_key: str | None = None


class AuroraAuthContext(BaseModel):
    user_id: uuid.UUID | None = None
    scopes: list[str] = Field(default_factory=list)
    source: str = "anonymous"
    key_prefix: str | None = None
