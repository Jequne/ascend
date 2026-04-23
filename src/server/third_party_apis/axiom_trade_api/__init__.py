"""
Axiom Trade API Client Library

A high-level Python client for interacting with Axiom Trade API with WebSocket support.

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

__version__ = "0.1.0"

from .client import AxiomTradeClient
from .models.auth import AxiomAgentData

__all__ = [
    "AxiomTradeClient",
    "AxiomAgentData",
]
