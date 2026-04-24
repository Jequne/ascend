from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass


@dataclass(slots=True)
class ParsedApiKey:
    prefix: str
    key_id: str
    secret: str


class SecretHasher:
    def __init__(self, iterations: int = 210_000, salt_bytes: int = 16):
        self.iterations = iterations
        self.salt_bytes = salt_bytes

    def create_salt(self) -> str:
        return secrets.token_hex(self.salt_bytes)

    def hash_secret(self, secret: str, salt: str) -> str:
        derived = hashlib.pbkdf2_hmac(
            "sha256",
            secret.encode("utf-8"),
            salt.encode("utf-8"),
            self.iterations,
        )
        encoded = base64.urlsafe_b64encode(derived).decode("ascii").rstrip("=")
        return encoded

    def create_secret_hash(self, secret: str, salt: str | None = None) -> tuple[str, str]:
        salt_value = salt or self.create_salt()
        return salt_value, self.hash_secret(secret, salt_value)

    def verify(self, secret: str, salt: str, expected_hash: str) -> bool:
        candidate = self.hash_secret(secret, salt)
        return hmac.compare_digest(candidate, expected_hash)


class ApiKeyCodec:
    def __init__(self, prefix: str = "ak"):
        self.prefix = prefix

    def issue(self, key_id: str, secret: str) -> str:
        return f"{self.prefix}_{key_id}.{secret}"

    def parse(self, access_key: str) -> ParsedApiKey:
        if not access_key:
            raise ValueError("access key is empty")

        prefix_and_id, separator, secret = access_key.partition(".")
        if not separator or not secret:
            raise ValueError("invalid access key format")

        prefix, separator, key_id = prefix_and_id.partition("_")
        if not separator or not key_id:
            raise ValueError("invalid access key format")

        if prefix != self.prefix:
            raise ValueError("invalid access key prefix")

        return ParsedApiKey(prefix=prefix, key_id=key_id, secret=secret)