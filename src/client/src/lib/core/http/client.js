import { API_CONFIG } from '../../config/api.js';
import { APIError, NetworkError } from '../errors/index.js';

export async function httpClient(endpoint, options = {}) {
    const url = `${API_CONFIG.baseUrl}${endpoint}`;

    const headers = {
        ...API_CONFIG.headers,
        ...options.headers
    };

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.timeout);

    try {
        const response = await fetch(url, {
            ...options,
            headers,
            signal: controller.signal
        });

        const data = await response.json().catch(() => null);

        if (!response.ok) {
            const errorMessage = data?.detail || data?.message || `Server error: ${response.status}`;
            throw new APIError(errorMessage, response.status, data);
        }

        return data;
    } catch (error) {
        if (error instanceof APIError) {
            throw error;
        }

        if (error.name === 'AbortError') {
            throw new NetworkError('Request timeout. Please try again.');
        }

        throw new NetworkError(error.message || 'Network error occurred');
    } finally {
        clearTimeout(timeoutId);
    }
}
