from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.api_key import ApiKey
from backend.app.models.user import User
from backend.app.utils.crypto import CryptoBox


class ApiKeyService:
    def __init__(self, *, db: AsyncSession, crypto: CryptoBox) -> None:
        self.db = db
        self.crypto = crypto

    async def ensure_user(self, user_id: uuid.UUID) -> User:
        res = await self.db.execute(select(User).where(User.id == user_id))
        user = res.scalar_one_or_none()
        if user:
            return user
        user = User(id=user_id)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def upsert_key(self, *, user_id: uuid.UUID, provider: str, api_key: str) -> None:
        await self.ensure_user(user_id)
        res = await self.db.execute(
            select(ApiKey).where(ApiKey.user_id == user_id, ApiKey.provider == provider)
        )
        existing = res.scalar_one_or_none()
        encrypted = self.crypto.encrypt(api_key)
        if existing:
            existing.encrypted_key = encrypted
            await self.db.commit()
            return
        self.db.add(ApiKey(user_id=user_id, provider=provider, encrypted_key=encrypted))
        await self.db.commit()

    async def get_decrypted_key(self, *, user_id: uuid.UUID, provider: str) -> str | None:
        res = await self.db.execute(
            select(ApiKey).where(ApiKey.user_id == user_id, ApiKey.provider == provider)
        )
        row = res.scalar_one_or_none()
        if not row:
            return None
        return self.crypto.decrypt(row.encrypted_key)

