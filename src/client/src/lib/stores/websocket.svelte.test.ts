import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/svelte";
import TokenCard from "$lib/components/TokenCard.svelte";
import {
    createLastDeployedToken,
    createTokenFeed,
} from "$lib/components/tokenFeed.fixture";
import { DEFAULT_FILTERS } from "$lib/config/constants";
import type { AutoOpenDispatcher } from "$lib/services/autoOpen";
import type { AudioNotificationPlayer } from "$lib/services/audioNotifications";
import { filtersStore } from "$lib/stores/filters.svelte";
import {
    WebSocketStore,
    type WebSocketFactory,
} from "$lib/stores/websocket.svelte";
import type { TokenFeedPayload } from "$lib/types";

class FakeWebSocket {
    onopen: ((event: Event) => void) | null = null;
    onmessage: ((event: MessageEvent<unknown>) => void) | null = null;
    onclose: ((event: CloseEvent) => void) | null = null;
    onerror: ((event: Event) => void) | null = null;
    closeCalls = 0;

    constructor(readonly url: string) {}

    open(): void {
        this.onopen?.(new Event("open"));
    }

    receive(value: unknown): void {
        this.onmessage?.(new MessageEvent("message", { data: value }));
    }

    close(): void {
        this.closeCalls += 1;
        this.onclose?.(new CloseEvent("close"));
    }

    fail(): void {
        this.onerror?.(new Event("error"));
    }
}

function createPayload(
    overrides: Partial<TokenFeedPayload> = {},
): TokenFeedPayload {
    const { clientKey, indicators, ...payload } = createTokenFeed();
    void clientKey;
    void indicators;
    return { ...payload, ...overrides };
}

function tokenMessage(overrides: Partial<TokenFeedPayload> = {}): string {
    return JSON.stringify({
        type: "token_feed",
        payload: createPayload(overrides),
    });
}

function createHarness(
    dispatcher: AutoOpenDispatcher,
    notificationPlayer: AudioNotificationPlayer = {
        play: vi.fn().mockResolvedValue(undefined),
    },
): {
    store: WebSocketStore;
    sockets: FakeWebSocket[];
} {
    const sockets: FakeWebSocket[] = [];
    const factory: WebSocketFactory = (url) => {
        const socket = new FakeWebSocket(url);
        sockets.push(socket);
        return socket as unknown as WebSocket;
    };
    return {
        store: new WebSocketStore(dispatcher, factory, notificationPlayer),
        sockets,
    };
}

beforeEach(() => {
    filtersStore.updateFilters({
        ...DEFAULT_FILTERS,
        autoOpenMode: "new_tab",
    });
});

afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
});

describe("WebSocketStore realtime pipeline", () => {
    it.each(["new_tab", "current_axiom_tab"] as const)(
        "blocks future developer tokens after blacklisting a funding card in %s mode",
        async (autoOpenMode) => {
            filtersStore.autoOpenMode = autoOpenMode;
            const dispatch = vi.fn<AutoOpenDispatcher["dispatch"]>();
            const play = vi
                .fn<AudioNotificationPlayer["play"]>()
                .mockResolvedValue(undefined);
            const { store, sockets } = createHarness({ dispatch }, { play });
            store.connect();
            const socket = sockets[0];
            socket?.open();
            const fundingPayload = createPayload({
                migrated_tokens_count: 0,
                last_deployed_tokens: null,
                funding_wallet: "funding-wallet",
                funding_migrated_tokens_count: 1,
                funding_all_tokens_count: 2,
                funding_deployed_tokens: [createLastDeployedToken()],
            });
            socket?.receive(tokenMessage(fundingPayload));
            const feed = store.tokenFeeds[0];
            expect(feed?.indicators).toEqual(["Dev Funding"]);
            if (!feed) throw new Error("Expected an accepted funding token");
            render(TokenCard, { feed });

            socket?.receive(
                tokenMessage({
                    pair_address: "pending-pair",
                    last_deployed_tokens: null,
                    migrated_tokens_count: 0,
                }),
            );
            const button = screen.getByRole("button", {
                name: "Add developer wallet to blacklist",
            });
            await fireEvent.click(button);
            expect(filtersStore.blacklist).toEqual([fundingPayload.dev_wallet]);

            socket?.receive(
                tokenMessage({
                    ...fundingPayload,
                    pair_address: "pending-pair",
                }),
            );
            socket?.receive(
                tokenMessage({
                    ...fundingPayload,
                    pair_address: "blocked-funding-pair",
                }),
            );
            socket?.receive(
                tokenMessage({ pair_address: "blocked-migration-pair" }),
            );
            expect(dispatch).toHaveBeenCalledOnce();
            expect(play).toHaveBeenCalledOnce();
            expect(store.tokenFeeds).toHaveLength(1);

            socket?.receive(
                tokenMessage({
                    ...fundingPayload,
                    pair_address: "other-dev-pair",
                    dev_wallet: "other-creator",
                }),
            );
            expect(dispatch).toHaveBeenCalledTimes(2);

            await fireEvent.click(button);
            socket?.receive(
                tokenMessage({
                    ...fundingPayload,
                    pair_address: "unblocked-pair",
                }),
            );
            expect(dispatch).toHaveBeenCalledTimes(3);
            expect(play).toHaveBeenCalledTimes(3);
            expect(store.tokenFeeds).toHaveLength(3);
            store.disconnect();
        },
    );

    it("accepts a token after developer and funding updates arrive in either order", () => {
        const dispatch = vi.fn<AutoOpenDispatcher["dispatch"]>();
        const { store, sockets } = createHarness({ dispatch });
        filtersStore.updateFilters({
            ...DEFAULT_FILTERS,
            autoOpenMode: "new_tab",
            fundingEnabled: true,
        });
        store.connect();
        sockets[0]?.open();
        const base = createPayload({
            all_tokens_count: 0,
            migrated_tokens_count: 0,
            last_deployed_tokens: null,
        });
        sockets[0]?.receive(tokenMessage(base));
        expect(store.tokenFeeds).toHaveLength(0);

        sockets[0]?.receive(
            tokenMessage({
                ...base,
                funding_wallet: "funding-wallet",
                funding_all_tokens_count: 2,
                funding_migrated_tokens_count: 1,
                funding_deployed_tokens: [createLastDeployedToken()],
            }),
        );
        sockets[0]?.receive(
            tokenMessage({
                ...base,
                all_tokens_count: 2,
                migrated_tokens_count: 1,
                last_deployed_tokens: [createLastDeployedToken()],
            }),
        );

        expect(store.tokenFeeds).toHaveLength(1);
        expect(store.tokenFeeds[0]?.funding_wallet).toBe("funding-wallet");
        expect(store.tokenFeeds[0]?.all_tokens_count).toBe(2);
        expect(dispatch).toHaveBeenCalledOnce();
        expect(store.tokenFeedTotalCount).toBe(1);
    });

    it("notifies once only after a token passes filters", () => {
        const dispatch = vi.fn<AutoOpenDispatcher["dispatch"]>();
        const play = vi
            .fn<AudioNotificationPlayer["play"]>()
            .mockResolvedValue(undefined);
        const { store, sockets } = createHarness({ dispatch }, { play });

        store.connect();
        sockets[0]?.open();
        sockets[0]?.receive(
            JSON.stringify({
                type: "ping",
                payload: { timestamp: new Date().toISOString() },
            }),
        );
        sockets[0]?.receive(
            JSON.stringify({ type: "sol_price", payload: 150 }),
        );
        sockets[0]?.receive(tokenMessage({ dev_holds_percent: null }));
        expect(play).not.toHaveBeenCalled();

        sockets[0]?.receive(tokenMessage());
        expect(play).toHaveBeenCalledOnce();
        expect(play).toHaveBeenCalledWith(
            expect.objectContaining({ enabled: true, volume: 70 }),
        );

        store.clearTokens();
        store.disconnect();
        expect(play).toHaveBeenCalledOnce();
    });

    it("parses once and invokes opener synchronously before updating accepted state", () => {
        let acceptedCountAtOpen = -1;
        let totalCountAtOpen = -1;
        const dispatch = vi.fn<AutoOpenDispatcher["dispatch"]>(() => {
            acceptedCountAtOpen = store.tokenFeedCount;
            totalCountAtOpen = store.tokenFeedTotalCount;
        });
        const { store, sockets } = createHarness({ dispatch });
        const parse = vi.spyOn(JSON, "parse");
        const timer = vi.spyOn(globalThis, "setTimeout");
        const windowOpen = vi.spyOn(window, "open");

        store.connect();
        const socket = sockets[0];
        expect(socket).toBeDefined();
        socket?.open();
        socket?.receive(tokenMessage());

        expect(parse).toHaveBeenCalledOnce();
        expect(dispatch).toHaveBeenCalledOnce();
        expect(acceptedCountAtOpen).toBe(0);
        expect(totalCountAtOpen).toBe(0);
        expect(store.tokenFeedCount).toBe(1);
        expect(store.tokenFeedTotalCount).toBe(1);
        expect(store.tokenFeeds).toHaveLength(1);
        expect(timer).not.toHaveBeenCalled();
        expect(windowOpen).not.toHaveBeenCalled();

        socket?.receive(tokenMessage({ dev_holds_percent: null }));
        expect(dispatch).toHaveBeenCalledOnce();
        expect(store.tokenFeedCount).toBe(1);
        expect(store.tokenFeedTotalCount).toBe(1);

        socket?.receive(tokenMessage());
        expect(dispatch).toHaveBeenCalledOnce();
        expect(store.tokenFeeds).toHaveLength(1);

        store.clearTokens();
        expect(store.tokenFeeds).toEqual([]);
        expect(store.tokenFeedCount).toBe(1);
        expect(store.tokenFeedTotalCount).toBe(1);
        expect(store.isConnected).toBe(true);
    });

    it("updates one card after late funding and triggers one notification and opener", () => {
        const dispatch = vi.fn<AutoOpenDispatcher["dispatch"]>();
        const play = vi
            .fn<AudioNotificationPlayer["play"]>()
            .mockResolvedValue(undefined);
        const { store, sockets } = createHarness({ dispatch }, { play });
        store.connect();
        sockets[0]?.open();

        sockets[0]?.receive(tokenMessage({ migrated_tokens_count: 0 }));
        expect(store.tokenFeeds).toHaveLength(0);
        expect(store.tokenFeedTotalCount).toBe(1);

        const fundingUpdate = tokenMessage({
            migrated_tokens_count: 0,
            funding_wallet: "funding-wallet",
            funding_migrated_tokens_count: 1,
            funding_all_tokens_count: 2,
            funding_deployed_tokens: [createLastDeployedToken()],
        });
        sockets[0]?.receive(fundingUpdate);
        sockets[0]?.receive(fundingUpdate);
        expect(store.tokenFeeds).toHaveLength(1);
        expect(store.tokenFeeds[0]?.indicators).toEqual(["Dev Funding"]);
        expect(store.tokenFeedCount).toBe(1);
        expect(store.tokenFeedTotalCount).toBe(1);
        expect(dispatch).toHaveBeenCalledOnce();
        expect(play).toHaveBeenCalledOnce();
    });

    it("adds a late funding indicator to an existing card without repeating effects", () => {
        const dispatch = vi.fn<AutoOpenDispatcher["dispatch"]>();
        const play = vi
            .fn<AudioNotificationPlayer["play"]>()
            .mockResolvedValue(undefined);
        const { store, sockets } = createHarness({ dispatch }, { play });
        store.connect();
        sockets[0]?.open();
        sockets[0]?.receive(tokenMessage());
        const firstKey = store.tokenFeeds[0]?.clientKey;

        sockets[0]?.receive(
            tokenMessage({
                funding_wallet: "funding-wallet",
                funding_migrated_tokens_count: 1,
                funding_all_tokens_count: 2,
                funding_deployed_tokens: [createLastDeployedToken()],
            }),
        );
        expect(store.tokenFeeds).toHaveLength(1);
        expect(store.tokenFeeds[0]?.clientKey).toBe(firstKey);
        expect(store.tokenFeeds[0]?.indicators).toEqual([
            "Dev Migrations",
            "Dev Funding",
        ]);
        expect(store.tokenFeedCount).toBe(1);
        expect(store.tokenFeedTotalCount).toBe(1);
        expect(dispatch).toHaveBeenCalledOnce();
        expect(play).toHaveBeenCalledOnce();
    });

    it("keeps verified funding when an older base message arrives later", () => {
        const dispatch = vi.fn<AutoOpenDispatcher["dispatch"]>();
        const play = vi
            .fn<AudioNotificationPlayer["play"]>()
            .mockResolvedValue(undefined);
        const { store, sockets } = createHarness({ dispatch }, { play });
        store.connect();
        sockets[0]?.open();

        const base = tokenMessage({ migrated_tokens_count: 0 });
        sockets[0]?.receive(base);
        sockets[0]?.receive(
            tokenMessage({
                migrated_tokens_count: 0,
                funding_wallet: "funding-wallet",
                funding_migrated_tokens_count: 1,
                funding_all_tokens_count: 2,
                funding_deployed_tokens: [createLastDeployedToken()],
            }),
        );
        sockets[0]?.receive(base);

        expect(store.tokenFeeds).toHaveLength(1);
        expect(store.tokenFeeds[0]?.indicators).toEqual(["Dev Funding"]);
        expect(store.tokenFeeds[0]?.funding_deployed_tokens).toHaveLength(1);
        expect(store.tokenFeeds[0]?.funding_migrated_tokens_count).toBe(1);
        expect(store.tokenFeedCount).toBe(1);
        expect(store.tokenFeedTotalCount).toBe(1);
        expect(dispatch).toHaveBeenCalledOnce();
        expect(play).toHaveBeenCalledOnce();
    });

    it("keeps rendering after invalid URLs, malformed JSON, and opener rejection", async () => {
        const rejection = new Error("dispatcher unavailable");
        const dispatch = vi.fn<AutoOpenDispatcher["dispatch"]>(() => {
            throw rejection;
        });
        const consoleError = vi
            .spyOn(console, "error")
            .mockImplementation(() => undefined);
        const { store, sockets } = createHarness({ dispatch });

        store.connect();
        const socket = sockets[0];
        socket?.open();
        socket?.receive("{");
        expect(store.tokenFeedTotalCount).toBe(0);

        socket?.receive(tokenMessage());
        expect(store.tokenFeeds).toHaveLength(1);
        expect(store.tokenFeedCount).toBe(1);
        expect(consoleError).toHaveBeenCalledWith(
            "Failed to dispatch token URL:",
            rejection,
        );

        socket?.receive(tokenMessage({ pair_address: "" }));
        expect(dispatch).toHaveBeenCalledTimes(2);
        expect(store.tokenFeeds).toHaveLength(2);
        expect(store.isConnected).toBe(true);

        socket?.fail();
        expect(consoleError).toHaveBeenCalledWith(
            "WS error:",
            expect.any(Event),
        );
        expect(store.isConnected).toBe(true);
    });

    it("handles ping, price, reconnect, and manual disconnect lifecycle", () => {
        vi.useFakeTimers();
        vi.setSystemTime(new Date("2026-08-11T12:00:00.100Z"));
        const dispatch = vi.fn<AutoOpenDispatcher["dispatch"]>();
        const { store, sockets } = createHarness({ dispatch });

        store.connect();
        sockets[0]?.open();
        sockets[0]?.receive(
            JSON.stringify({
                type: "ping",
                payload: { timestamp: "2026-08-11T12:00:00.000Z" },
            }),
        );
        sockets[0]?.receive(
            JSON.stringify({ type: "sol_price", payload: "184.2" }),
        );

        expect(store.ping).toBe(100);
        expect(store.solPrice).toBe("184.2");
        sockets[0]?.close();
        expect(store.isConnected).toBe(false);
        expect(vi.getTimerCount()).toBe(1);

        vi.advanceTimersByTime(3000);
        expect(sockets).toHaveLength(2);
        sockets[1]?.open();
        expect(store.isConnected).toBe(true);

        store.disconnect();
        expect(sockets[1]?.closeCalls).toBe(1);
        expect(store.isConnected).toBe(false);
        expect(vi.getTimerCount()).toBe(0);

        vi.advanceTimersByTime(3000);
        expect(sockets).toHaveLength(2);
    });
});
