from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from backend.app.core.config import get_settings
from backend.app.core.logging import configure_logging
from backend.app.db.init_db import init_db
from backend.app.db.session import async_session, engine
from backend.app.routes.apikey import router as apikey_router
from backend.app.routes.chat import router as chat_router
from backend.app.routes.memory import router as memory_router
from backend.app.routes.skills import router as skills_router
from backend.app.routes.tools import router as tools_router
from backend.app.services.skill_engine import SkillEngine
from backend.app.services.vector_store import ChromaVectorStore, InMemoryVectorStore
from backend.app.utils.crypto import CryptoBox

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, default_response_class=ORJSONResponse)

    app.include_router(chat_router)
    app.include_router(skills_router)
    app.include_router(memory_router)
    app.include_router(apikey_router)
    app.include_router(tools_router)

    @app.get("/healthz", tags=["health"])
    async def healthz() -> dict:
        return {"ok": True}

    @app.on_event("startup")
    async def startup() -> None:
        configure_logging()
        logger.info("Starting %s (%s)", settings.app_name, settings.app_env)

        app.state.crypto = CryptoBox.from_master_key(settings.master_key)
        if settings.vector_backend == "chroma":
            app.state.vector_store = ChromaVectorStore(persist_dir=str(settings.chroma_persist_dir))
        else:
            app.state.vector_store = InMemoryVectorStore()

        await init_db(engine)
        async with async_session() as db:
            await SkillEngine(db).ensure_builtin_skills()

    @app.on_event("shutdown")
    async def shutdown() -> None:
        await engine.dispose()

    return app


app = create_app()
