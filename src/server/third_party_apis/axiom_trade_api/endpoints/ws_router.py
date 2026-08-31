import asyncio
import inspect
import logging
from typing import Any, Awaitable, Callable, Dict, Set, TypeAlias

from pydantic import ValidationError

from ..models import (
    NewPairsRoomMessage,
    SolPriceRoomMessage,
)


logger = logging.getLogger(__name__)

MessageCallback: TypeAlias = Callable[[Any], Any]
MessageCallbackDecorator: TypeAlias = Callable[
    [MessageCallback],
    MessageCallback,
]


class WebsocketMessageRouter:
    def __init__(self) -> None:
        self._callbacks: Dict[str, Set[MessageCallback]] = {}

    def on(self, room: str) -> MessageCallbackDecorator:
        """Register a callback for a websocket room."""

        def decorator(callback: MessageCallback) -> MessageCallback:
            self._callbacks.setdefault(room, set()).add(callback)
            return callback

        return decorator

    def register_callback(
        self,
        room: str,
        callback: MessageCallback,
    ) -> None:
        self._callbacks.setdefault(room, set()).add(callback)

    def unregister_callback(
        self,
        room: str,
        callback: MessageCallback,
    ) -> None:
        callbacks = self._callbacks.get(room)

        if not callbacks:
            return

        callbacks.discard(callback)

        if not callbacks:
            self._callbacks.pop(room, None)

    def validate_room_message(
        self,
        data: Dict[str, Any],
    ) -> Any | None:
        room = data.get("room")

        match room:
            case "sol_price":
                model = SolPriceRoomMessage

            case "new_pairs":
                model = NewPairsRoomMessage

            case _:
                return data

        try:
            return model.model_validate(data)

        except ValidationError as exc:
            logger.warning(
                "Skipping invalid websocket message for room %s: %s",
                room,
                exc,
            )
            return None

    async def dispatch_message(
        self,
        data: Any,
    ) -> None:
        if hasattr(data, "room"):
            room = data.room
        elif isinstance(data, dict):
            room = data.get("room")
        else:
            logger.debug(
                "Skipping websocket message without room information"
            )
            return

        if not room:
            return

        callbacks = self._callbacks.get(room)

        if not callbacks:
            return

        async_callbacks: list[
            tuple[MessageCallback, Awaitable[Any]]
        ] = []

        for callback in callbacks:
            try:
                result = callback(data)

            except Exception:
                logger.exception(
                    "Callback failed for websocket room %s: %r",
                    room,
                    callback,
                )
                continue

            if inspect.isawaitable(result):
                async_callbacks.append(
                    (callback, result)
                )

        if not async_callbacks:
            return

        results = await asyncio.gather(
            *(awaitable for _, awaitable in async_callbacks),
            return_exceptions=True,
        )

        for (callback, _), result in zip(
            async_callbacks,
            results,
        ):
            if isinstance(result, BaseException):
                logger.error(
                    "Async callback failed for websocket room %s: %r",
                    room,
                    callback,
                    exc_info=(
                        type(result),
                        result,
                        result.__traceback__,
                    ),
                )