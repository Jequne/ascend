import { getStoredKey } from "$lib/api/auth";
import { WS_BASE_URL } from "$lib/config/constants";
import {
    autoOpenDispatcher,
    type AutoOpenDispatcher,
} from "$lib/services/autoOpen";
import {
    audioNotificationService,
    type AudioNotificationPlayer,
} from "$lib/services/audioNotifications";
import { filtersStore } from "$lib/stores/filters.svelte";
import { notificationsStore } from "$lib/stores/notifications.svelte";
import type { FilterSnapshot, TokenFeed } from "$lib/types";
import { evaluateTokenFeed, prependRollingFeed } from "$lib/utils/feed";
import { parseWebSocketMessage } from "$lib/utils/websocketMessage";
import { SvelteMap } from "svelte/reactivity";

export type WebSocketFactory = (url: string) => WebSocket;
const MAX_SEEN_TOKENS = 10_000;

export class WebSocketStore {
    private ws: WebSocket | null = null;
    private shouldReconnect = false;
    private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
    private feedSequence = 0;
    private seenTokens = new SvelteMap<
        string,
        { clientKey: string; accepted: boolean }
    >();

    isConnected = $state(false);
    isConnecting = $state(false);
    ping = $state(0);
    solPrice = $state<number | string | null>(null);
    tokenFeedCount = $state(0);
    tokenFeedTotalCount = $state(0);
    tokenFeeds = $state<TokenFeed[]>([]);

    constructor(
        private readonly dispatcher: AutoOpenDispatcher = autoOpenDispatcher,
        private readonly createSocket: WebSocketFactory = (url) =>
            new WebSocket(url),
        private readonly notificationPlayer: AudioNotificationPlayer = audioNotificationService,
    ) {}

    private openAcceptedFeed(feed: TokenFeed, snapshot: FilterSnapshot): void {
        try {
            this.dispatcher.dispatch(feed, snapshot);
        } catch (error: unknown) {
            console.error("Failed to dispatch token URL:", error);
        }
    }

    private notifyAcceptedFeed(): void {
        try {
            void this.notificationPlayer
                .play(notificationsStore.settings)
                .catch((error: unknown) => {
                    console.warn("Failed to play token notification:", error);
                });
        } catch (error: unknown) {
            console.warn("Failed to play token notification:", error);
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

        const incoming = message.payload;
        const tokenId = incoming.pair_address || incoming.token_address;
        const existing = this.tokenFeeds.find(
            (feed) => (feed.pair_address || feed.token_address) === tokenId,
        );
        // Funding enrichment never retracts a previously verified history.
        // A delayed base message must not erase a newer funding result.
        const payload =
            existing?.funding_wallet && incoming.funding_wallet == null
                ? {
                      ...incoming,
                      funding_wallet: existing.funding_wallet,
                      funding_deployed_tokens: existing.funding_deployed_tokens,
                      funding_migrated_tokens_count:
                          existing.funding_migrated_tokens_count,
                      funding_all_tokens_count:
                          existing.funding_all_tokens_count,
                  }
                : incoming;
        const seen = this.seenTokens.get(tokenId);
        const clientKey = seen?.clientKey ?? `${tokenId}:${this.feedSequence}`;
        const snapshot = filtersStore.snapshot;
        const decision = evaluateTokenFeed(payload, snapshot, clientKey);

        if (!seen) {
            this.feedSequence += 1;
            this.seenTokens.set(tokenId, { clientKey, accepted: false });
            if (this.seenTokens.size > MAX_SEEN_TOKENS) {
                const oldest = this.seenTokens.keys().next().value;
                if (oldest !== undefined) this.seenTokens.delete(oldest);
            }
        }

        if (!decision.accepted) {
            if (!seen) this.tokenFeedTotalCount += 1;
            return;
        }

        if (seen?.accepted) {
            this.tokenFeeds = this.tokenFeeds.map((feed) =>
                feed.clientKey === clientKey ? decision.feed : feed,
            );
            return;
        }

        this.seenTokens.set(tokenId, { clientKey, accepted: true });
        this.openAcceptedFeed(decision.feed, snapshot);
        if (!seen) this.tokenFeedTotalCount += 1;
        this.tokenFeedCount += 1;
        this.tokenFeeds = prependRollingFeed(this.tokenFeeds, decision.feed);
        this.notifyAcceptedFeed();
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
        this.seenTokens.clear();
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
