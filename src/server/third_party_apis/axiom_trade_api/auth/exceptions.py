class AxiomError(Exception):
    pass


class AxiomAuthError(AxiomError):
    pass


class AxiomRefreshTokenError(AxiomAuthError):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class AxiomAccessTokenError(AxiomAuthError):
    pass
