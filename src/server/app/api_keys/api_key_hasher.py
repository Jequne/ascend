import hashlib

from ..config import settings


class ApiKeyHasher():

    @staticmethod
    def hash(api_key: str) -> str:
        pepper = settings.api_key_pepper or ""
        payload = f"{pepper}{api_key}".encode("utf-8")

        return hashlib.sha256(payload).hexdigest()
