import { getStoredKey } from "$lib/api/auth";
import { WS_BASE_URL } from "$lib/config/constants";
import { openerService, type UrlOpener } from "$lib/services/opener";
import { filtersStore } from "$lib/stores/filters.svelte";
import type { FilterSnapshot, TokenFeed } from "$lib/types";
import { evaluateTokenFeed, prependRollingFeed } from "$lib/utils/feed";
import { buildTerminalUrl } from "$lib/utils/tokenLinks";
import { parseWebSocketMessage } from "$lib/utils/websocketMessage";

export type WebSocketFactory = (url: string) => WebSocket;

export class WebSocketStore {
    private ws: WebSocket | null = null;
    private shouldReconnect = false;
    private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
    private feedSequence = 0;

    isConnected = $state(false);
    isConnecting = $state(false);
    ping = $state(0);
    solPrice = $state<number | string | null>(null);
    tokenFeedCount = $state(0);
    tokenFeedTotalCount = $state(0);
    tokenFeeds = $state<TokenFeed[]>([]);

    constructor(
        private readonly opener: UrlOpener = openerService,
        private readonly createSocket: WebSocketFactory = (url) =>
            new WebSocket(url),
    ) {}

    private openAcceptedFeed(feed: TokenFeed, snapshot: FilterSnapshot): void {
        if (!snapshot.filters.autoOpenInNewTab) return;

        const url = buildTerminalUrl(feed, snapshot.filters.terminal);
        if (!url) return;

        try {
            void this.opener.open(url).catch((error: unknown) => {
                console.error("Failed to open token URL:", error);
            });
        } catch (error: unknown) {
            console.error("Failed to open token URL:", error);
        }
    }

    private handleMessage(rawData: unknown): void {
        const message = parseWebSocketMessage(rawData);
        if (!message) return;

        if (message.type === "ping") {
            const serverTime = Date.parse(message.payload.timestamp);
            this.ping = Math.abs(Date.now() - serverTime);
            return;
        }

        if (message.type === "sol_price") {
            this.solPrice = message.payload;
            return;
        }

        const payload = message.payload;
        const clientKey = `${payload.pair_address || payload.token_address}:${this.feedSequence}`;
        const snapshot = filtersStore.snapshot;
        const decision = evaluateTokenFeed(payload, snapshot, clientKey);

        if (!decision.accepted) {
            this.tokenFeedTotalCount += 1;
            return;
        }

        this.openAcceptedFeed(decision.feed, snapshot);
        this.feedSequence += 1;
        this.tokenFeedTotalCount += 1;
        this.tokenFeedCount += 1;
        this.tokenFeeds = prependRollingFeed(this.tokenFeeds, decision.feed);
    }

    connect = (): void => {
        if (this.ws) return;

        this.isConnecting = true;
        this.shouldReconnect = true;

        try {
            const ws = this.createSocket(
                `${WS_BASE_URL}?api_key=${getStoredKey() ?? ""}`,
            );
            this.ws = ws;

            ws.onopen = () => {
                if (this.ws !== ws) return;
                this.isConnected = true;
                this.isConnecting = false;
            };

            ws.onmessage = (event: MessageEvent<unknown>) => {
                if (this.ws === ws) this.handleMessage(event.data);
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
                        this.reconnectTimeout = null;
                        this.connect();
                    }, 3000);
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
