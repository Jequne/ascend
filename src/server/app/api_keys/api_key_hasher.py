import hashlib


class ApiKeyHasher:
    def __init__(self, pepper: str):
        self._pepper = pepper

    def hash(self, api_key: str) -> str:
        payload = f"{self._pepper}{api_key}".encode("utf-8")

        return hashlib.sha256(payload).hexdigest()
