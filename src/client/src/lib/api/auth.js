import { httpClient } from '../core/http/index.js';
import { ENDPOINTS } from '../config/api.js';
import { ValidationError } from '../core/errors/index.js';

export async function validateApiKey(apiKey) {
    if (!apiKey || typeof apiKey !== 'string') {
        throw new ValidationError('API key must be a non-empty string');
    }

    return httpClient(ENDPOINTS.validateKey, {
        method: 'POST',
        headers: {
            'X-API-Key': apiKey.trim()
        }
    });
}