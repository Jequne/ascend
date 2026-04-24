import asyncio
import logging
from typing import Optional, Dict, Set, Callable, Any

from pydantic import ValidationError

from ..models.websockets.subscription_message import (
    NewPairsRoomMessage,
    SolPriceRoomMessage,
)


logger = logging.getLogger(__name__)


class WebsocketMessageRouter:
    def __init__(self):
        self._callbacks: Dict[str, Set[Callable[[Any], Any]]] = {}

    def on(self, room: str):
        """Decorator to register callback for a room."""

        def decorator(callback: Callable[[Any], Any]) -> Callable:
            self._callbacks.setdefault(room, set()).add(callback)
            return callback

        return decorator

    def register_callback(
            self,
            room: str,
            callback: Callable[[Any], Any],
            ) -> None:
        self._callbacks.setdefault(room, set()).add(callback)

    def unregister_callback(
            self,
            room: str,
            callback: Callable[[Any], Any],
            ) -> None:
        callbacks = self._callbacks.get(room)
        if not callbacks:
            return

        callbacks.discard(callback)
        if not callbacks:
            self._callbacks.pop(room, None)

    def validate_room_message(self, data: Dict[str, Any]) -> Optional[Any]:
        room = data.get("room")
        model = None

        match room:
            case "sol_price":
                model = SolPriceRoomMessage
            case "new_pairs":
                model = NewPairsRoomMessage
            case _:
                return data

        try:
            return model.model_validate(data)

        except ValidationError as e:
            logger.warning(
                "🟨 Skip invalid websocket message for room %s: %s",
                room,
                e,
            )
            return None

    async def dispatch_message(self, data: Any) -> None:
        room = data.room if hasattr(data, "room") else data.get("room")
        if not room:
            return

        callbacks = self._callbacks.get(room)
        if not callbacks:
            return

        async_tasks = []
        for callback in callbacks:
            try:
                result = callback(data)
                if asyncio.iscoroutine(result):
                    async_tasks.append(result)

            except Exception as e:
                logger.error(
                    "🟨 callback error for room %s: %s",
                    room,
                    e,
                )

        if async_tasks:
            await asyncio.gather(*async_tasks, return_exceptions=True)