class AuthError(Exception):
    pass


class AuthenticationError(AuthError):
    pass


class AuthorizationError(AuthError):
    pass


class AccessKeyFormatError(AuthenticationError):
    pass


class AccessKeyNotFoundError(AuthenticationError):
    pass


class AccessKeyInactiveError(AuthenticationError):
    pass


class AccessKeyExpiredError(AuthenticationError):
    pass