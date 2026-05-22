import { getStoredKey } from "$lib/api/auth.js";
import {
    WS_BASE_URL,
    DEFAULT_FILTERS,
} from "$lib/config/constants.js";
import { filtersStore } from "$lib/stores/filters.svelte.js";
import { passesLastTokenFeesFilter } from "$lib/utils/lastTokenFees.js";
import { passesLastTokensFilter } from "$lib/utils/lastTokens.js";

class WebSocketStore {
    ws = null;
    isConnected = $state(false);
    isConnecting = $state(false);
    ping = $state(0);
    solPrice = $state(null);
    // tokenFeedCount: messages that passed filters (filtered)
    tokenFeedCount = $state(0);
    // tokenFeedTotalCount: total incoming token_feed messages (regardless of filters)
    tokenFeedTotalCount = $state(0);
    tokenFeeds = $state([]);
    shouldReconnect = false;
    reconnectTimeout = null;

    passesFeesFilter = (lastDeployedTokens) => {
        const feesMode = filtersStore.feesMode ?? DEFAULT_FILTERS.feesMode;
        const minLastTokenFees = Number(
            filtersStore.minLastTokenFees ?? DEFAULT_FILTERS.minLastTokenFees,
        );
        return passesLastTokenFeesFilter(lastDeployedTokens, {
            mode: feesMode,
            minFeeThreshold: minLastTokenFees,
        });
    };

    passesLastTokensFilter = (lastDeployedTokens) => {
        const minLastTokenAthMcap = Number(
            filtersStore.minLastTokenAthMcap ??
            DEFAULT_FILTERS.minLastTokenAthMcap,
        );
        const lastTokensRequiredCount = Number(
            filtersStore.lastTokensRequiredCount ??
            DEFAULT_FILTERS.lastTokensRequiredCount,
        );

        return passesLastTokensFilter(lastDeployedTokens, {
            minAthMcapThreshold: minLastTokenAthMcap,
            requiredCount: lastTokensRequiredCount,
        });
    };

    connect = () => {
        if (this.ws) return;

        this.isConnecting = true;
        this.shouldReconnect = true;
        const key = getStoredKey();

        try {
            const ws = new WebSocket(`${WS_BASE_URL}?api_key=${key}`);
            this.ws = ws;

            ws.onopen = () => {
                if (this.ws !== ws) return;
                this.isConnected = true;
                this.isConnecting = false;
            };

            ws.onmessage = (event) => {
                if (this.ws !== ws) return;
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === "ping" && data.payload?.timestamp) {
                        const serverTime = new Date(data.payload.timestamp).getTime();
                        const clientTime = Date.now();
                        this.ping = Math.abs(clientTime - serverTime);
                    } else if (data.type === "sol_price") {
                        this.solPrice = data.payload;
                    } else if (data.type === "token_feed") {
                        // Always increment the total incoming counter
                        this.tokenFeedTotalCount++;

                        try {
                            const payload = data.payload;

                            const minDev = Number(filtersStore.minDevHoldsPercent ?? DEFAULT_FILTERS.minDevHoldsPercent);
                            const maxDev = Number(filtersStore.maxDevHoldsPercent ?? DEFAULT_FILTERS.maxDevHoldsPercent);
                            const minMigration = Number(filtersStore.minMigrationPercent ?? DEFAULT_FILTERS.minMigrationPercent);

                            const dev = payload?.dev_holds_percent;
                            const allTokens = Number(payload?.all_tokens_count) || 0;
                            const migrated = Number(payload?.migrated_tokens_count) || 0;
                            const migrationPercent = allTokens > 0 ? (migrated / allTokens) * 100 : 0;
                            const feesPass = this.passesFeesFilter(payload?.last_deployed_tokens);
                            const lastTokensPass = this.passesLastTokensFilter(payload?.last_deployed_tokens);

                            const devPass = dev !== null && dev !== undefined && !Number.isNaN(dev) && dev >= minDev && dev <= maxDev;
                            const migrationPass = !Number.isNaN(migrationPercent) && migrationPercent >= minMigration;

                            if (devPass && feesPass && (migrationPass || lastTokensPass)) {
                                // Increment filtered counter and add to visible feed list
                                this.tokenFeedCount++;
                                this.tokenFeeds = [
                                    {
                                        ...payload,
                                        indicators: [
                                            ...(payload?.indicator ? [payload.indicator] : []),
                                            ...(lastTokensPass ? ["last tokens"] : []),
                                        ],
                                    },
                                    ...this.tokenFeeds,
                                ];
                            }
                        } catch (e) {
                            // On error, count as total but don't add to filtered list
                        }
                    }
                } catch (e) { }
            };

            ws.onclose = () => {
                if (this.ws !== ws) return;
                this.isConnected = false;
                this.isConnecting = false;
                this.ws = null;
                this.ping = 0;
                this.solPrice = null;

                if (this.shouldReconnect) {
                    this.reconnectTimeout = setTimeout(() => {
                        this.connect();
                    }, 3000);
                }
            };

            ws.onerror = (err) => {
                if (this.ws !== ws) return;
                console.error("WS error:", err);
            };
        } catch (e) {
            console.error("Failed to create WS:", e);
            this.isConnecting = false;
        }
    }

    disconnect = () => {
        this.shouldReconnect = false;
        if (this.reconnectTimeout) {
            clearTimeout(this.reconnectTimeout);
            this.reconnectTimeout = null;
        }
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.isConnected = false;
        this.isConnecting = false;
        this.ping = 0;
        this.tokenFeedCount = 0;
        this.tokenFeedTotalCount = 0;
        this.tokenFeeds = [];
    }

    toggleConnection = () => {
        if (this.isConnected || this.isConnecting || this.shouldReconnect) {
            this.disconnect();
        } else {
            this.connect();
        }
    }

    clearTokens = () => {
        this.tokenFeeds = [];
    }
}

export const wsStore = new WebSocketStore();