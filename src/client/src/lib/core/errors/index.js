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
        return error.message;
    }

    if (error instanceof NetworkError) {
        return 'Network error. Please check your connection.';
    }

    if (error instanceof ValidationError) {
        return error.message;
    }

    if (error instanceof Error) {
        return error.message;
    }

    return defaultMessage;
}
