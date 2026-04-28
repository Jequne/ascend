from __future__ import annotations

import hashlib
import secrets

from ..config import settings


def hash_api_key(raw_key: str) -> str:
    pepper = settings.api_key_pepper or ""
    payload = f"{pepper}{raw_key}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def generate_api_key() -> tuple[str, str]:
    """Return (raw_key, kid) in format asc_<kid>_<secret>."""
    kid = secrets.token_hex(6)
    secret = secrets.token_urlsafe(24)
    raw = f"asc_{kid}_{secret}"
    return raw, kid


def parse_prefixed_api_key(raw: str) -> tuple[str, str] | None:
    """
    Expect asc_<kid>_<secret>. Secret may contain underscores;
    split only first two underscores.
    """
    raw = raw.strip()
    parts = raw.split("_", 2)
    if len(parts) != 3 or parts[0] != "asc":
        return None
    kid, secret = parts[1], parts[2]
    if not kid or not secret:
        return None
    return kid, raw
