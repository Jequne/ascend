from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class AccessResult:
    status: Literal["valid", "invalid", "expired", "revoked"]
    kid: str | None = None
    max_active_sessions: int = 1


@dataclass(frozen=True, slots=True)
class WsAuthContext:
    raw_key: str
    kid: str
    max_active_sessions: int


def extract_raw_api_key(
    *,
    body_key: str | None = None,
    authorization: str | None = None,
    x_api_key: str | None = None,
) -> str | None:
    if body_key:
        return body_key.strip() or None
    if x_api_key:
        return x_api_key.strip() or None
    if authorization:
        scheme, sep, credentials = authorization.strip().partition(" ")
        if sep and scheme.lower() == "bearer":
            return credentials.strip() or None
    return None
