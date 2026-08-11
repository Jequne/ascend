import { API_BASE_URL } from "$lib/config/constants";
import { isPlainObject } from "$lib/config/settings";

const API_URL = `${API_BASE_URL}/auth/validate-key`;
const LICENSE_STORAGE_KEY = "license_key";

export async function validateKey(apiKey: string): Promise<boolean> {
    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ api_key: apiKey }),
        });
        const data: unknown = await response.json();
        return response.ok && isPlainObject(data) && data.status === "valid";
    } catch (error: unknown) {
        console.error("Validation error:", error);
        return false;
    }
}

export function getStoredKey(): string | null {
    return localStorage.getItem(LICENSE_STORAGE_KEY);
}

export function storeKey(key: string): void {
    localStorage.setItem(LICENSE_STORAGE_KEY, key);
}

export function clearKey(): void {
    localStorage.removeItem(LICENSE_STORAGE_KEY);
}
