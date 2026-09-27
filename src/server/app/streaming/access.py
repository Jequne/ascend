import asyncio

from .contracts import AccessChecker, Connection
from .domain import WsAuthContext
from .sessions import ConnectionManager


class AuthStreamingProcessor:
    def __init__(self, access: AccessChecker, manager: ConnectionManager):
        self._access = access
        self._manager = manager

    @staticmethod
    async def send_error_and_close(
        connection: Connection, reason: str, code: int = 1008
    ) -> None:
        try:
            await connection.send_json({"type": "error", "payload": {"reason": reason}})
        except Exception:
            pass
        try:
            await connection.close(code=code)
        except Exception:
            pass

    async def connect_if_allowed(
        self, connection: Connection, raw_key: str | None
    ) -> WsAuthContext | None:
        if not raw_key:
            await self.send_error_and_close(
                connection, "the api key was not transferred"
            )
            return None
        result = await self._access.validate(raw_key)
        if result is None or result.status != "valid" or not result.kid:
            await self.send_error_and_close(connection, "api key is not valid")
            return None
        if (
            await self._manager.active_sessions_for_kid(result.kid)
            >= result.max_active_sessions
        ):
            await self.send_error_and_close(connection, "too_many_sessions")
            return None
        await self._manager.connect(connection, kid=result.kid)
        return WsAuthContext(raw_key, result.kid, result.max_active_sessions)

    async def ws_key_watchdog(
        self,
        *,
        connection: Connection,
        raw_key: str,
        stop: asyncio.Event,
        interval_seconds: float = 30.0,
    ) -> None:
        while not stop.is_set():
            await asyncio.sleep(interval_seconds)
            check = await self._access.validate(raw_key)
            if check and check.status == "valid":
                continue
            # Preserve the documented legacy failure on a database outage.
            if check is None:
                raise AttributeError("'NoneType' object has no attribute 'status'")
            reason = {
                "invalid": "invalid_key",
                "expired": "expired",
                "revoked": "revoked",
            }.get(check.status, "invalid_key")
            await self.send_error_and_close(connection, reason)
            stop.set()
            break
