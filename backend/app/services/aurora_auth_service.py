from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timezone

from fastapi import Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import AuroraApiKey
from app.schemas.aurora_auth import AuroraAuthContext, AuroraKeyResponse
from app.services.api_key_service import ApiKeyService


class AuroraAuthService:
    def __init__(self, *, db: AsyncSession, api_keys: ApiKeyService) -> None:
        self.db = db
        self.api_keys = api_keys
        self.settings = get_settings()

    @staticmethod
    def _hash_key(raw_key: str) -> str:
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    @staticmethod
    def _prefix(raw_key: str) -> str:
        return raw_key[:18]

    async def issue_key(self, *, user_id: uuid.UUID, name: str, scopes: list[str]) -> AuroraKeyResponse:
        await self.api_keys.ensure_user(user_id)
        raw_key = f"aurora_live_{secrets.token_urlsafe(24)}"
        row = AuroraApiKey(
            user_id=str(user_id),
            name=name,
            key_prefix=self._prefix(raw_key),
            key_hash=self._hash_key(raw_key),
            scopes=scopes,
            is_active=True,
        )
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return AuroraKeyResponse(
            id=row.id,
            user_id=row.user_id,
            name=row.name,
            key_prefix=row.key_prefix,
            scopes=row.scopes or [],
            is_active=row.is_active,
            api_key=raw_key,
        )

    async def list_keys(self, *, user_id: uuid.UUID) -> list[AuroraKeyResponse]:
        result = await self.db.execute(
            select(AuroraApiKey).where(AuroraApiKey.user_id == str(user_id)).order_by(AuroraApiKey.created_at.desc())
        )
        rows = list(result.scalars().all())
        return [
            AuroraKeyResponse(
                id=row.id,
                user_id=row.user_id,
                name=row.name,
                key_prefix=row.key_prefix,
                scopes=row.scopes or [],
                is_active=row.is_active,
                api_key=None,
            )
            for row in rows
        ]

    async def validate_key(self, raw_key: str) -> AuroraAuthContext | None:
        result = await self.db.execute(
            select(AuroraApiKey).where(
                AuroraApiKey.key_hash == self._hash_key(raw_key),
                AuroraApiKey.is_active.is_(True),
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        row.last_used_at = datetime.now(timezone.utc)
        await self.db.commit()
        return AuroraAuthContext(
            user_id=row.user_id,
            scopes=row.scopes or [],
            source="aurora_api_key",
            key_prefix=row.key_prefix,
        )

    async def get_demo_key(self, *, user_id: uuid.UUID | None = None) -> AuroraKeyResponse | None:
        if not self.settings.test_mode_enabled:
            return None
        demo_key = self.settings.test_default_aurora_key
        if not demo_key:
            return None
        resolved_user = user_id or self.settings.test_default_user_id
        if resolved_user is None:
            return None
        await self.api_keys.ensure_user(resolved_user)
        existing = await self.validate_key(demo_key)
        if existing is None:
            row = AuroraApiKey(
                user_id=resolved_user,
                name="demo",
                key_prefix=self._prefix(demo_key),
                key_hash=self._hash_key(demo_key),
                scopes=["run", "skills", "tools", "memory"],
                is_active=True,
            )
            self.db.add(row)
            await self.db.commit()
            await self.db.refresh(row)
            return AuroraKeyResponse(
                id=row.id,
                user_id=row.user_id,
                name=row.name,
                key_prefix=row.key_prefix,
                scopes=row.scopes or [],
                is_active=row.is_active,
                api_key=demo_key,
            )
        rows = await self.list_keys(user_id=resolved_user)
        for row in rows:
            if row.key_prefix == self._prefix(demo_key):
                row.api_key = demo_key
                return row
        return None


async def resolve_aurora_auth(
    *,
    db: AsyncSession,
    api_keys: ApiKeyService,
    authorization: str | None,
    x_aurora_key: str | None,
) -> AuroraAuthContext:
    settings = get_settings()
    service = AuroraAuthService(db=db, api_keys=api_keys)
    raw_key = None
    if authorization and authorization.lower().startswith("bearer "):
        raw_key = authorization.split(" ", 1)[1].strip()
    elif x_aurora_key:
        raw_key = x_aurora_key.strip()

    if raw_key:
        ctx = await service.validate_key(raw_key)
        if ctx is None:
            raise HTTPException(status_code=401, detail="Invalid Aurora API key.")
        return ctx

    if settings.test_mode_enabled and settings.test_default_aurora_key:
        demo = await service.validate_key(settings.test_default_aurora_key)
        if demo:
            return demo
        await service.get_demo_key()
        demo = await service.validate_key(settings.test_default_aurora_key)
        if demo:
            return demo

    raise HTTPException(status_code=401, detail="Missing Aurora API key.")


async def aurora_auth_dependency(
    db: AsyncSession,
    api_keys: ApiKeyService,
    authorization: str | None = Header(default=None),
    x_aurora_key: str | None = Header(default=None),
) -> AuroraAuthContext:
    return await resolve_aurora_auth(
        db=db,
        api_keys=api_keys,
        authorization=authorization,
        x_aurora_key=x_aurora_key,
    )
