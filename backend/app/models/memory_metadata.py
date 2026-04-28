from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, JSON, func
from app.db.types import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MemoryMetadata(Base):
    __tablename__ = "memory_metadata"

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(), ForeignKey("users.id"), index=True)
    memory_scope: Mapped[str] = mapped_column(String(32), default="user", index=True)
    context_key: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(), ForeignKey("conversations.id"), index=True, nullable=True
    )
    kind: Mapped[str] = mapped_column(String(32), index=True)  # arbitrary tag
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
