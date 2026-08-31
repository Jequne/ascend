class InvalidApiKeyFormat(Exception):
    ...


class ApiKeyNotFoundError(Exception):
    ...


class ApiKeyAlreadyExistsError(Exception):
    ...


class InvalidApiKeyError(Exception):
    ...


class ApiKeyExpirationError(Exception):
    ...


class ApiKeyRevocationError(Exception):
    ...