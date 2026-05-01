export class APIError extends Error {
    constructor(message, statusCode, details = null) {
        super(message);
        this.name = 'APIError';
        this.statusCode = statusCode;
        this.details = details;
    }
}

export class NetworkError extends Error {
    constructor(message) {
        super(message);
        this.name = 'NetworkError';
    }
}

export class ValidationError extends Error {
    constructor(message, field = null) {
        super(message);
        this.name = 'ValidationError';
        this.field = field;
    }
}

export function parseErrorMessage(error, defaultMessage = 'An error occurred') {
    if (error instanceof APIError) {
        if (error.details && error.details.status) {
            const statusMessages = {
                'invalid': 'Invalid API key. Please check and try again.',
                'expired': 'This API key has expired.',
                'revoked': 'This API key has been revoked by the administrator.',
                'rate_limited': 'Too many attempts. Please wait a moment.'
            };
            return statusMessages[error.details.status] || error.message || defaultMessage;
        }
        return error.message || defaultMessage;
    }

    if (error instanceof NetworkError) {
        return 'Network connection problem. Please check your internet.';
    }

    if (error instanceof ValidationError) {
        return error.message;
    }

    if (error instanceof Error) {
        return error.message;
    }

    return defaultMessage;
}
