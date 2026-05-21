from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from .manager import ConnectionManager
from ...schemas.ws_streaming import WsStreamingResponse
from ...services.tokens_prices.sol_price import \
    sol_price_broadcast_starter


logger = logging.getLogger(__name__)


def sol_price_broadcaster(
        sol_price_broadcast_starter=sol_price_broadcast_starter
) -> None:
    sol_price_broadcast_starter.start()
    
        
        