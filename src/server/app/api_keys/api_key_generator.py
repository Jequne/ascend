import secrets
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class GeneratedApiKey:
    kid: str
    secret: str

    @property
    def api_key(self) -> str:
        return f"asc_{self.kid}_{self.secret}"


class ApiKeyGenerator():

    @staticmethod
    def generate() -> GeneratedApiKey:
        api_key_id = secrets.token_hex(6)
        api_key_secret = secrets.token_urlsafe(24)

        return GeneratedApiKey(
            kid=api_key_id,
            secret=api_key_secret
        )