"""
Axiom Trade API Client Library

A high-level Python client for interacting with Axiom Trade API
with WebSocket support.

Usage:
    from axiom_trade_api import AxiomTradeClient, AxiomAgentData

    client = AxiomTradeClient()
    agent = AxiomAgentData.create_with_flat_params(
        auth_refresh_token="...",
        auth_access_token="...",
        user_agent="..."
    )

    client.add_agents([agent])
    client.connect_websocket()
    client.on_sol_price(lambda data: print(data))

    # Use the client...
    await client.close()
"""

from .auth.exceptions import AxiomAccessTokenError, AxiomRefreshTokenError
from .client import AxiomTradeClient
from .endpoints.exceptions import (
    AxiomHTTPStatusError,
    AxiomRequestError,
    AxiomWebSocketError,
)
from .models import (
    AxiomAgentData,
    DevTokensV3Response,
    NewPairsRoomMessage,
    PairChartV2Params,
    PairChartV2Response,
    PairInfoResponse,
    SolPriceRoomMessage,
    Token,
    TokenInfoResponse,
)
from .request_pacer import background_axiom_request

__version__ = "0.1.0"
__all__ = [
    "AuthManager",
    "AxiomTradeEndpoints",
    "AxiomTradeWebsocket",
    "RoomSubscribeRequest",
    "AxiomTradeClient",
    "AxiomAgentData",
    "NewPairsRoomMessage",
    "SolPriceRoomMessage",
    "DevTokensV3Response",
    "Token",
    "PairInfoResponse",
    "TokenInfoResponse",
    "PairChartV2Params",
    "PairChartV2Response",
    "background_axiom_request",
    "AxiomHTTPStatusError",
    "AxiomRequestError",
    "AxiomWebSocketError",
    "AxiomRefreshTokenError",
    "AxiomAccessTokenError",
]

from .auth import AuthManager
from .endpoints import AxiomTradeEndpoints, AxiomTradeWebsocket
from .models import RoomSubscribeRequest
