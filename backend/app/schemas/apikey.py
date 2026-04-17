from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field


class ApiKeySaveRequest(BaseModel):
    user_id: uuid.UUID
    provider: Literal["openai", "anthropic", "openrouter"]
    api_key: str = Field(min_length=5)


class ApiKeySaveResponse(BaseModel):
    user_id: uuid.UUID
    provider: str
    stored: bool = True
