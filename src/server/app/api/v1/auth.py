from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Header, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_async_db
from ...schemas.auth import ValidateKeyRequest, ValidateKeyResponse
from ...services.auth import AuthServicer

router = APIRouter()


@router.post("/auth/validate-key", response_model=ValidateKeyResponse)
async def validate_key(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_async_db),
    body: ValidateKeyRequest | None = Body(None),
    authorization: str | None = Header(None),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
) -> ValidateKeyResponse:
    return await AuthServicer.validate_key(
        request=request,
        response=response,
        db=db,
        body=body,
        authorization=authorization,
        x_api_key=x_api_key,
    )

