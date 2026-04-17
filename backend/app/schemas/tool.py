from __future__ import annotations

from pydantic import BaseModel, Field


class ToolDescriptor(BaseModel):
    name: str
    description: str
    input_schema: dict = Field(default_factory=dict)

