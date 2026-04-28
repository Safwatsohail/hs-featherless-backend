from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.api_key import ApiKey
from app.models.user import User
from app.utils.crypto import CryptoBox


class ApiKeyService:
    def __init__(self, *, db: AsyncSession, crypto: CryptoBox) -> None:
        self.db = db
        self.crypto = crypto

    async def ensure_user(self, user_id: uuid.UUID) -> User:
        uid_str = str(user_id)
        res = await self.db.execute(select(User).where(User.id == uid_str))
        user = res.scalar_one_or_none()
        if user:
            return user
        try:
            user = User(id=uid_str)
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except Exception:
            await self.db.rollback()
            res = await self.db.execute(select(User).where(User.id == uid_str))
            return res.scalar_one()

    async def upsert_key(self, *, user_id: uuid.UUID, provider: str, api_key: str) -> None:
        await self.ensure_user(user_id)
        uid_str = str(user_id)
        res = await self.db.execute(
            select(ApiKey).where(ApiKey.user_id == uid_str, ApiKey.provider == provider)
        )
        existing = res.scalar_one_or_none()
        encrypted = self.crypto.encrypt(api_key)
        if existing:
            existing.encrypted_key = encrypted
            await self.db.commit()
            return
        self.db.add(ApiKey(user_id=uid_str, provider=provider, encrypted_key=encrypted))
        await self.db.commit()

    async def get_decrypted_key(self, *, user_id: uuid.UUID, provider: str) -> str | None:
        uid_str = str(user_id)
        res = await self.db.execute(
            select(ApiKey).where(ApiKey.user_id == uid_str, ApiKey.provider == provider)
        )
        row = res.scalar_one_or_none()
        if row:
            return self.crypto.decrypt(row.encrypted_key)

        settings = get_settings()
        if (
            settings.test_mode_enabled
            and settings.test_default_provider == provider
            and settings.test_default_api_key
        ):
            return settings.test_default_api_key

        return None
