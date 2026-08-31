class AxiomError(Exception):
    pass


class AxiomApiError(AxiomError):
    pass


class AxiomRequestError(AxiomApiError):
    """Failed to perform the HTTP request."""


class AxiomHTTPStatusError(AxiomApiError):
    """The API returned an unexpected HTTP status code."""


class AxiomResponseError(AxiomApiError):
    """The API returned an invalid response."""


class AxiomResponseValidationError(AxiomResponseError):
    """The API response does not match the expected Pydantic model."""


class AxiomWebSocketError(AxiomError):
    pass


class AxiomWebSocketConnectionError(AxiomWebSocketError):
    """Failed to establish a WebSocket connection."""


class AxiomWebSocketNotConnectedError(AxiomWebSocketError):
    """WebSocket operation requires an active connection."""


class AxiomWebSocketSubscriptionError(AxiomWebSocketError):
    """Failed to subscribe to a WebSocket room."""


class AxiomWebSocketReceiveError(AxiomWebSocketError):
    """Failed while receiving WebSocket messages."""


class AxiomWebSocketCloseError(AxiomWebSocketError):
    """Failed to close the WebSocket connection."""