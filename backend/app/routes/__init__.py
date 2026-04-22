from backend.app.routes.apikey import router as apikey_router
from backend.app.routes.aurora_auth import router as aurora_auth_router
from backend.app.routes.chat import router as chat_router
from backend.app.routes.memory import router as memory_router
from backend.app.routes.public_api import public_router, router as public_api_router
from backend.app.routes.skills import router as skills_router
from backend.app.routes.tools import router as tools_router
from backend.app.routes.web import router as web_router

__all__ = [
    "apikey_router",
    "aurora_auth_router",
    "chat_router",
    "memory_router",
    "public_api_router",
    "public_router",
    "skills_router",
    "tools_router",
    "web_router",
]
