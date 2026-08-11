import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createTokenFeed } from "$lib/components/tokenFeed.fixture";
import { DEFAULT_FILTERS } from "$lib/config/constants";
import type { UrlOpener } from "$lib/services/opener";
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

function createHarness(opener: UrlOpener): {
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
        store: new WebSocketStore(opener, factory),
        sockets,
    };
}

beforeEach(() => {
    filtersStore.updateFilters({
        ...DEFAULT_FILTERS,
        autoOpenInNewTab: true,
    });
});

afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
});

describe("WebSocketStore realtime pipeline", () => {
    it("parses once and invokes opener synchronously before updating accepted state", () => {
        let acceptedCountAtOpen = -1;
        let totalCountAtOpen = -1;
        const open = vi.fn<(url: string) => Promise<void>>(() => {
            acceptedCountAtOpen = store.tokenFeedCount;
            totalCountAtOpen = store.tokenFeedTotalCount;
            return Promise.resolve();
        });
        const { store, sockets } = createHarness({ open });
        const parse = vi.spyOn(JSON, "parse");
        const timer = vi.spyOn(globalThis, "setTimeout");
        const windowOpen = vi.spyOn(window, "open");

        store.connect();
        const socket = sockets[0];
        expect(socket).toBeDefined();
        socket?.open();
        socket?.receive(tokenMessage());

        expect(parse).toHaveBeenCalledOnce();
        expect(open).toHaveBeenCalledOnce();
        expect(open).toHaveBeenCalledWith(
            "https://axiom.trade/meme/pair?chain=sol",
        );
        expect(acceptedCountAtOpen).toBe(0);
        expect(totalCountAtOpen).toBe(0);
        expect(store.tokenFeedCount).toBe(1);
        expect(store.tokenFeedTotalCount).toBe(1);
        expect(store.tokenFeeds).toHaveLength(1);
        expect(timer).not.toHaveBeenCalled();
        expect(windowOpen).not.toHaveBeenCalled();

        socket?.receive(tokenMessage({ dev_holds_percent: null }));
        expect(open).toHaveBeenCalledOnce();
        expect(store.tokenFeedCount).toBe(1);
        expect(store.tokenFeedTotalCount).toBe(2);

        socket?.receive(tokenMessage());
        expect(open).toHaveBeenCalledTimes(2);
        expect(store.tokenFeeds).toHaveLength(2);

        store.clearTokens();
        expect(store.tokenFeeds).toEqual([]);
        expect(store.tokenFeedCount).toBe(2);
        expect(store.tokenFeedTotalCount).toBe(3);
        expect(store.isConnected).toBe(true);
    });

    it("keeps rendering after invalid URLs, malformed JSON, and opener rejection", async () => {
        const rejection = new Error("opener unavailable");
        const open = vi
            .fn<(url: string) => Promise<void>>()
            .mockRejectedValue(rejection);
        const consoleError = vi
            .spyOn(console, "error")
            .mockImplementation(() => undefined);
        const { store, sockets } = createHarness({ open });

        store.connect();
        const socket = sockets[0];
        socket?.open();
        socket?.receive("{");
        expect(store.tokenFeedTotalCount).toBe(0);

        socket?.receive(tokenMessage());
        expect(store.tokenFeeds).toHaveLength(1);
        expect(store.tokenFeedCount).toBe(1);
        await Promise.resolve();
        expect(consoleError).toHaveBeenCalledWith(
            "Failed to open token URL:",
            rejection,
        );

        socket?.receive(tokenMessage({ pair_address: "" }));
        expect(open).toHaveBeenCalledOnce();
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
        const open = vi
            .fn<(url: string) => Promise<void>>()
            .mockResolvedValue();
        const { store, sockets } = createHarness({ open });

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
