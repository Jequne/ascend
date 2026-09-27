from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app import api_keys

from ..domain import AccessResult


class ApiKeysAccess:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        manager_factory: Callable[[AsyncSession], api_keys.ApiKeyManager],
    ):
        self._sessions = sessions
        self._manager_factory = manager_factory

    async def validate(self, raw_key: str) -> AccessResult | None:
        try:
            async with self._sessions() as session:
                manager = self._manager_factory(session)
                try:
                    result = await manager.validate(raw_key)
                except api_keys.ApiKeyExpirationError:
                    await session.commit()
                    return AccessResult("expired")
                except api_keys.ApiKeyRevocationError:
                    await session.commit()
                    return AccessResult("revoked")
                except (
                    api_keys.ApiKeyNotFoundError,
                    api_keys.InvalidApiKeyError,
                    api_keys.InvalidApiKeyFormat,
                ):
                    return AccessResult("invalid")
                await session.commit()
                return AccessResult("valid", result.kid, result.max_active_sessions)
        except Exception:
            return None
