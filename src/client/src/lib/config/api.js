import { PUBLIC_API_BASE_URL } from '$env/static/public';

export const API_CONFIG = {
    baseUrl: PUBLIC_API_BASE_URL,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json'
    }
};

export const ENDPOINTS = {
    validateKey: '/api/v1/auth/validate-key'
};
