from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncEngine

from app.db.base import Base
from app.models import (  # noqa: F401
    ApiKey,
    AuroraApiKey,
    Conversation,
    ExternalTool,
    MemoryMetadata,
    Message,
    Skill,
    User,
)

logger = logging.getLogger(__name__)


async def init_db(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("DB schema ensured (create_all).")
