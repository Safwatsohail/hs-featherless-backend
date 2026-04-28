from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field


class ApiKeySaveRequest(BaseModel):
    user_id: str
    provider: Literal["openai", "anthropic", "featherless", "openrouter"]
    api_key: str = Field(min_length=5)


class ApiKeySaveResponse(BaseModel):
    user_id: str
    provider: str
    stored: bool = True
