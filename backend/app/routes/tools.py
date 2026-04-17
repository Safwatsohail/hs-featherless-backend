from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import get_settings
from backend.app.db.session import get_db
from backend.app.schemas.tool import ToolDescriptor
from backend.app.services.tool_engine import ToolEngine

router = APIRouter(prefix="/tools", tags=["tools"])


@router.get("", response_model=list[ToolDescriptor])
async def list_tools(db: AsyncSession = Depends(get_db)) -> list[ToolDescriptor]:
    settings = get_settings()
    engine = ToolEngine(
        db=db,
        python_timeout_seconds=settings.python_tool_timeout_seconds,
        bash_timeout_seconds=settings.bash_tool_timeout_seconds,
        http_timeout_seconds=settings.http_tool_timeout_seconds,
        web_search_max_results=settings.web_search_max_results,
        deep_search_max_pages=settings.deep_search_max_pages,
    )
    return engine.list_tools()

