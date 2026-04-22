from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from backend.app.core.config import get_settings
from backend.app.core.logging import configure_logging
from backend.app.db.init_db import init_db
from backend.app.db.session import async_session, engine
from backend.app.routes.apikey import router as apikey_router
from backend.app.routes.aurora_auth import router as aurora_auth_router
from backend.app.routes.chat import router as chat_router
from backend.app.routes.memory import router as memory_router
from backend.app.routes.public_api import public_router, router as public_api_router
from backend.app.routes.skills import router as skills_router
from backend.app.routes.tools import router as tools_router
from backend.app.routes.web import router as web_router
from backend.app.services.cache_layer import CacheLayer
from backend.app.services.skill_engine import SkillEngine
from backend.app.services.vector_store import ChromaVectorStore, InMemoryVectorStore
from backend.app.utils.crypto import CryptoBox

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, default_response_class=ORJSONResponse)

    # Enable CORS for frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(chat_router)
    app.include_router(aurora_auth_router)
    app.include_router(public_router)
    app.include_router(public_api_router)
    app.include_router(skills_router)
    app.include_router(memory_router)
    app.include_router(apikey_router)
    app.include_router(tools_router)
    app.include_router(web_router)
    
    # Import and include streaming router
    from backend.app.routes.streaming import router as streaming_router
    app.include_router(streaming_router)

    @app.get("/healthz", tags=["health"])
    async def healthz() -> dict:
        return {"ok": True}

    @app.on_event("startup")
    async def startup() -> None:
        configure_logging()
        logger.info("Starting %s (%s)", settings.app_name, settings.app_env)

        app.state.crypto = CryptoBox.from_master_key(settings.master_key)
        
        # Initialize cache layer
        redis_url = getattr(settings, 'redis_url', None)
        app.state.cache = CacheLayer(redis_url=redis_url)
        logger.info("Cache layer initialized (Redis: %s)", "enabled" if redis_url else "local-only")
        
        if settings.vector_backend == "chroma":
            app.state.vector_store = ChromaVectorStore(persist_dir=str(settings.chroma_persist_dir))
        else:
            app.state.vector_store = InMemoryVectorStore()

        await init_db(engine)
        async with async_session() as db:
            await SkillEngine(db).ensure_builtin_skills()
            logger.info("Skill system initialized with 1,080+ skills")

    @app.on_event("shutdown")
    async def shutdown() -> None:
        if hasattr(app.state, 'cache'):
            await app.state.cache.close()
        await engine.dispose()

    return app


app = create_app()
