from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from .provider import (
    AxiomTokenImageProvider,
    TokenImageProvider,
    TokenImageUpstreamError,
)


router = APIRouter(prefix="/token-images", tags=["token-images"])


def get_token_image_provider() -> TokenImageProvider:
    return AxiomTokenImageProvider()


@router.get("/{token_address}", response_class=Response)
async def get_token_image(
    token_address: str,
    provider: Annotated[
        TokenImageProvider,
        Depends(get_token_image_provider),
    ],
) -> Response:
    try:
        image = await provider.fetch(token_address)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except TokenImageUpstreamError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="token image provider unavailable",
        ) from exc

    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="token image not found",
        )

    return Response(
        content=image.content,
        media_type=image.media_type,
        headers={"Cache-Control": "public, max-age=3600"},
    )
