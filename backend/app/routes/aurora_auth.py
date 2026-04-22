from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db
from backend.app.schemas.aurora_auth import AuroraKeyIssueRequest, AuroraKeyResponse
from backend.app.services.api_key_service import ApiKeyService
from backend.app.services.aurora_auth_service import AuroraAuthService

router = APIRouter(prefix="/auth", tags=["aurora-auth"])


def _service(*, request: Request, db: AsyncSession) -> AuroraAuthService:
    api_keys = ApiKeyService(db=db, crypto=request.app.state.crypto)
    return AuroraAuthService(db=db, api_keys=api_keys)


@router.post("/issue-key", response_model=AuroraKeyResponse)
async def issue_aurora_key(
    payload: AuroraKeyIssueRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> AuroraKeyResponse:
    return await _service(request=request, db=db).issue_key(
        user_id=payload.user_id,
        name=payload.name,
        scopes=payload.scopes,
    )


@router.get("/keys", response_model=list[AuroraKeyResponse])
async def list_aurora_keys(
    user_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> list[AuroraKeyResponse]:
    return await _service(request=request, db=db).list_keys(user_id=user_id)


@router.get("/demo-key", response_model=AuroraKeyResponse | None)
async def get_demo_key(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> AuroraKeyResponse | None:
    return await _service(request=request, db=db).get_demo_key()
