import { getStoredKey } from "$lib/api/auth";
import { WS_BASE_URL } from "$lib/config/constants";
import { filtersStore } from "$lib/stores/filters.svelte";
import type { LastDeployedToken, TokenFeed } from "$lib/types";
import { tokenMatchesBlacklist } from "$lib/utils/blacklist";
import { passesLastTokenFeesFilter } from "$lib/utils/lastTokenFees";
import { passesLastTokensFilter } from "$lib/utils/lastTokens";
import { openTokenUrlInNewTab } from "$lib/utils/tokenLinks";
import { parseWebSocketMessage } from "$lib/utils/websocketMessage";

class WebSocketStore {
    private ws: WebSocket | null = null;
    private shouldReconnect = false;
    private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;

    isConnected = $state(false);
    isConnecting = $state(false);
    ping = $state(0);
    solPrice = $state<number | string | null>(null);
    tokenFeedCount = $state(0);
    tokenFeedTotalCount = $state(0);
    tokenFeeds = $state<TokenFeed[]>([]);

    private passesFeesFilter(
        lastDeployedTokens: readonly LastDeployedToken[] | null,
    ): boolean {
        return passesLastTokenFeesFilter(lastDeployedTokens, {
            mode: filtersStore.feesMode,
            minFeeThreshold: filtersStore.minLastTokenFees,
        });
    }

    private passesLastTokensFilter(
        lastDeployedTokens: readonly LastDeployedToken[] | null,
    ): boolean {
        return passesLastTokensFilter(lastDeployedTokens, {
            minAthMcapThreshold: filtersStore.minLastTokenAthMcap,
            requiredCount: filtersStore.lastTokensRequiredCount,
        });
    }

    connect = (): void => {
        if (this.ws) return;

        this.isConnecting = true;
        this.shouldReconnect = true;

        try {
            const ws = new WebSocket(
                `${WS_BASE_URL}?api_key=${getStoredKey() ?? ""}`,
            );
            this.ws = ws;

            ws.onopen = () => {
                if (this.ws !== ws) return;
                this.isConnected = true;
                this.isConnecting = false;
            };

            ws.onmessage = (event: MessageEvent<unknown>) => {
                if (this.ws !== ws) return;

                const message = parseWebSocketMessage(event.data);
                if (!message) return;

                if (message.type === "ping") {
                    const serverTime = new Date(
                        message.payload.timestamp,
                    ).getTime();
                    this.ping = Math.abs(Date.now() - serverTime);
                    return;
                }

                if (message.type === "sol_price") {
                    this.solPrice = message.payload;
                    return;
                }

                this.tokenFeedTotalCount += 1;
                const payload = message.payload;
                const allTokens = payload.all_tokens_count || 0;
                const migrated = payload.migrated_tokens_count || 0;
                const migrationPercent =
                    allTokens > 0 ? (migrated / allTokens) * 100 : 0;
                const feesPass = this.passesFeesFilter(
                    payload.last_deployed_tokens,
                );
                const lastTokensPass = this.passesLastTokensFilter(
                    payload.last_deployed_tokens,
                );
                const blacklistPass = !tokenMatchesBlacklist(
                    payload,
                    filtersStore.blacklistMatcher,
                );
                const devPass =
                    payload.dev_holds_percent !== null &&
                    payload.dev_holds_percent >=
                        filtersStore.minDevHoldsPercent &&
                    payload.dev_holds_percent <=
                        filtersStore.maxDevHoldsPercent;
                const migrationPass =
                    migrationPercent >= filtersStore.minMigrationPercent;

                if (
                    !blacklistPass ||
                    !devPass ||
                    !feesPass ||
                    (!migrationPass && !lastTokensPass)
                ) {
                    return;
                }

                const nextFeed: TokenFeed = {
                    ...payload,
                    indicators: [
                        ...(payload.indicator ? [payload.indicator] : []),
                        ...(lastTokensPass ? ["last tokens"] : []),
                    ],
                    last_deployed_tokens: payload.last_deployed_tokens ?? [],
                };

                this.tokenFeedCount += 1;

                if (
                    filtersStore.autoOpenInNewTab &&
                    filtersStore.aggressiveAutoOpen
                ) {
                    void openTokenUrlInNewTab(nextFeed, filtersStore.terminal);
                }

                this.tokenFeeds.unshift(nextFeed);

                if (
                    filtersStore.autoOpenInNewTab &&
                    !filtersStore.aggressiveAutoOpen
                ) {
                    setTimeout(() => {
                        void openTokenUrlInNewTab(
                            nextFeed,
                            filtersStore.terminal,
                        );
                    }, 0);
                }
            };

            ws.onclose = () => {
                if (this.ws !== ws) return;
                this.isConnected = false;
                this.isConnecting = false;
                this.ws = null;
                this.ping = 0;
                this.solPrice = null;

                if (this.shouldReconnect) {
                    this.reconnectTimeout = setTimeout(this.connect, 3000);
                }
            };

            ws.onerror = (error: Event) => {
                if (this.ws === ws) console.error("WS error:", error);
            };
        } catch (error: unknown) {
            console.error("Failed to create WS:", error);
            this.isConnecting = false;
        }
    };

    disconnect = (): void => {
        this.shouldReconnect = false;

        if (this.reconnectTimeout) {
            clearTimeout(this.reconnectTimeout);
            this.reconnectTimeout = null;
        }

        this.ws?.close();
        this.ws = null;
        this.isConnected = false;
        this.isConnecting = false;
        this.ping = 0;
        this.tokenFeedCount = 0;
        this.tokenFeedTotalCount = 0;
        this.tokenFeeds = [];
    };

    toggleConnection = (): void => {
        if (this.isConnected || this.isConnecting || this.shouldReconnect) {
            this.disconnect();
        } else {
            this.connect();
        }
    };

    clearTokens = (): void => {
        this.tokenFeeds = [];
    };
}

export const wsStore = new WebSocketStore();
