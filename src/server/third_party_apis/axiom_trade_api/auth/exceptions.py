class AxiomError(Exception):
    pass


class AxiomAuthError(AxiomError):
    pass


class AxiomRefreshTokenError(AxiomAuthError):
    pass


class AxiomAccessTokenError(AxiomAuthError):
    pass