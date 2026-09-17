import unittest

from curl_cffi.curl import CurlError

from third_party_apis.axiom_trade_api.endpoints.exceptions import (
    AxiomWebSocketReceiveError,
)
from third_party_apis.axiom_trade_api.endpoints.ws import AxiomTradeWebsocket


class _ResetWebSocket:
    def __aiter__(self):
        return self

    async def __anext__(self):
        raise CurlError("connection reset", 56)


class AxiomTradeWebsocketTests(unittest.IsolatedAsyncioTestCase):
    async def test_curl_receive_error_enters_reconnect_path(self) -> None:
        websocket = AxiomTradeWebsocket(
            auth_manager=None,
            endpoints=None,
        )
        websocket._wsocket = _ResetWebSocket()

        with self.assertRaises(AxiomWebSocketReceiveError):
            await websocket._messages_handler()


if __name__ == "__main__":
    unittest.main()
