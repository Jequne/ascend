"""Manual probe for the unmodified Axiom WebSocket payloads.

Run from src/server: python -m third_party_apis.axiom_trade_api.tests.manual_wss_probe --rooms new_pairs
Stop with Ctrl+C.
"""

import argparse
import asyncio
import sys

from curl_cffi import AsyncSession

from app.config import settings
from third_party_apis.axiom_trade_api.auth import AuthManager
from third_party_apis.axiom_trade_api.endpoints.endpoints import AxiomTradeEndpoints
from third_party_apis.axiom_trade_api.endpoints.ws import AxiomTradeWebsocket
from third_party_apis.axiom_trade_api.models.websockets.subscription_message import (
    RoomSubscribeRequest,
)


async def main(rooms: list[str]) -> None:
    agent = settings.axiom_api_config.load_axiom_api_agents()[0]
    session = AsyncSession()
    auth_manager = AuthManager()
    websocket = AxiomTradeWebsocket(
        auth_manager,
        AxiomTradeEndpoints(auth_manager),
    )

    try:
        await websocket.connect((session, agent))
        for room in rooms:
            await websocket.subscribe(RoomSubscribeRequest(room=room))

        print(f"Listening to: {', '.join(rooms)} (Ctrl+C to stop)", flush=True)
        async for payload in websocket.raw_messages():
            sys.stdout.buffer.write(payload + b"\n")
            sys.stdout.buffer.flush()
    finally:
        await websocket.close()
        await session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rooms",
        nargs="+",
        choices=("new_pairs", "sol_price", "migrations"),
        default=["new_pairs"],
        help="Axiom rooms to join (default: new_pairs)",
    )
    arguments = parser.parse_args()
    try:
        asyncio.run(main(arguments.rooms))
    except KeyboardInterrupt:
        pass
