from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.apikey import ApiKeySaveRequest, ApiKeySaveResponse
from app.services.api_key_service import ApiKeyService

router = APIRouter(tags=["apikey"])


@router.post("/apikey", response_model=ApiKeySaveResponse)
async def save_api_key(
    req: ApiKeySaveRequest, request: Request, db: AsyncSession = Depends(get_db)
) -> ApiKeySaveResponse:
    svc = ApiKeyService(db=db, crypto=request.app.state.crypto)
    await svc.upsert_key(user_id=req.user_id, provider=req.provider, api_key=req.api_key)
    return ApiKeySaveResponse(user_id=req.user_id, provider=req.provider)

