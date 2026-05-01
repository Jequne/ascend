// Simple localStorage wrapper for API key with expiry (TTL)
const STORAGE_KEY = "ascend_api_key_v1";

function nowMs() {
    return Date.now();
}

export function setApiKey(key, ttlMs = 7 * 24 * 60 * 60 * 1000) {
    if (!key) return;
    const record = {
        key,
        expiresAt: nowMs() + ttlMs,
    };
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(record));
    } catch (e) {
        console.warn("Failed to store api key:", e);
    }
}

export function getApiKey() {
    try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (!raw) return null;
        const record = JSON.parse(raw);
        if (!record || !record.key) return null;
        if (record.expiresAt && nowMs() > record.expiresAt) {
            // expired
            localStorage.removeItem(STORAGE_KEY);
            return null;
        }
        return record.key;
    } catch (e) {
        console.warn("Failed to read api key:", e);
        return null;
    }
}

export function clearApiKey() {
    try {
        localStorage.removeItem(STORAGE_KEY);
    } catch (e) {
        console.warn("Failed to clear api key:", e);
    }
}

export function isAuthorized() {
    return !!getApiKey();
}
