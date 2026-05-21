import { validateKey, getStoredKey, storeKey, clearKey } from "$lib/api/auth.js";

function createAuthStore() {
    let isLoading = $state(true);
    let isAuthenticated = $state(false);

    async function init() {
        isLoading = true;
        const storedKey = getStoredKey();
        if (storedKey) {
            const isValid = await validateKey(storedKey);
            if (isValid) {
                isAuthenticated = true;
            } else {
                clearKey();
            }
        }
        isLoading = false;
    }

    async function login(key) {
        const isValid = await validateKey(key);
        if (isValid) {
            storeKey(key);
            isAuthenticated = true;
            return true;
        }
        return false;
    }

    function logout() {
        clearKey();
        isAuthenticated = false;
    }

    return {
        get isLoading() { return isLoading; },
        get isAuthenticated() { return isAuthenticated; },
        init,
        login,
        logout
    };
}

export const authStore = createAuthStore();