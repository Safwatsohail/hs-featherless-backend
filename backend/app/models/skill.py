from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, JSON, func
from app.db.types import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(80), index=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    version: Mapped[str] = mapped_column(String(32), default="1.0.0")

    triggers: Mapped[list[str]] = mapped_column(JSON, default=list)
    prompt_template: Mapped[str] = mapped_column(String, nullable=False)
    tool_permissions: Mapped[list[str]] = mapped_column(JSON, default=list)
    memory_rules: Mapped[dict] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

