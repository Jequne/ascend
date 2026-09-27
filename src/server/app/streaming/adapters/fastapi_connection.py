from fastapi import WebSocket


class FastApiConnection:
    def __init__(self, websocket: WebSocket):
        self._websocket = websocket

    async def send_json(self, message: dict[str, object]) -> None:
        await self._websocket.send_json(message)

    async def close(self, code: int = 1008) -> None:
        await self._websocket.close(code=code)
