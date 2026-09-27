import unittest
from unittest.mock import patch

from curl_cffi.curl import CurlError

from third_party_apis.axiom_trade_api.endpoints.exceptions import (
    AxiomWebSocketReceiveError,
)
from third_party_apis.axiom_trade_api.endpoints.ws import AxiomTradeWebsocket

from ..auth import AuthManager
from ..endpoints import AxiomTradeEndpoints


class _ResetWebSocket:
    def __aiter__(self):
        return self

    async def __anext__(self):
        raise CurlError("connection reset", 56)


class _RawWebSocket:
    def __init__(self):
        self.messages = iter(
            (b'{"room":"new_pairs","unknown":1}', b"not JSON")
        )

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self.messages)
        except StopIteration:
            raise StopAsyncIteration


class AxiomTradeWebsocketTests(unittest.IsolatedAsyncioTestCase):
    async def test_raw_messages_keep_payloads_unchanged(self) -> None:
        websocket = AxiomTradeWebsocket(
            auth_manager=AuthManager(),
            endpoints=AxiomTradeEndpoints(AuthManager()),
        )
        patcher = patch.object(websocket, "_wsocket", _RawWebSocket())
        patcher.start()
        self.addCleanup(patcher.stop)

        messages = [message async for message in websocket.raw_messages()]

        self.assertEqual(
            messages,
            [b'{"room":"new_pairs","unknown":1}', b"not JSON"],
        )

    async def test_curl_receive_error_enters_reconnect_path(self) -> None:
        websocket = AxiomTradeWebsocket(
            auth_manager=AuthManager(),
            endpoints=AxiomTradeEndpoints(AuthManager()),
        )
        patcher = patch.object(websocket, "_wsocket", _ResetWebSocket())
        patcher.start()
        self.addCleanup(patcher.stop)

        with self.assertRaises(AxiomWebSocketReceiveError):
            await websocket._messages_handler()


if __name__ == "__main__":
    unittest.main()
