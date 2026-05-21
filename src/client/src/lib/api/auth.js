import { API_BASE_URL } from "$lib/config/constants.js";

const API_URL = `${API_BASE_URL}/auth/validate-key`;

/**
 * Проверяет валидность ключа через REST API.
 * @param {string} apiKey - ключ API для валидации
 * @returns {Promise<boolean>}
 */
export async function validateKey(apiKey) {
    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ api_key: apiKey })
        });
        const data = await response.json();
        return response.ok && data.status === "valid";
    } catch (error) {
        console.error("Validation error:", error);
        return false;
    }
}

/**
 * Возвращает сохраненный ключ.
 */
export function getStoredKey() {
    return localStorage.getItem("license_key");
}

/**
 * Сохраняет ключ в localStorage.
 * @param {string} key
 */
export function storeKey(key) {
    localStorage.setItem("license_key", key);
}

/**
 * Удаляет ключ (логаут).
 */
export function clearKey() {
    localStorage.removeItem("license_key");
}
