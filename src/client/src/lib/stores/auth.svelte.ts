import { clearKey, getStoredKey, storeKey, validateKey } from "$lib/api/auth";

class AuthStore {
    isLoading = $state(true);
    isAuthenticated = $state(false);

    async init(): Promise<void> {
        this.isLoading = true;
        const storedKey = getStoredKey();

        if (storedKey) {
            if (await validateKey(storedKey)) {
                this.isAuthenticated = true;
            } else {
                clearKey();
            }
        }

        this.isLoading = false;
    }

    async login(key: string): Promise<boolean> {
        if (!(await validateKey(key))) return false;

        storeKey(key);
        this.isAuthenticated = true;
        return true;
    }

    logout(): void {
        clearKey();
        this.isAuthenticated = false;
    }
}

export const authStore = new AuthStore();
