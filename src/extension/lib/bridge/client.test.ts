import { afterEach, describe, expect, it, vi } from "vitest";
import { ExtensionBridgeClient, type BridgeSocket } from "./client";

const pairingSecret = "a".repeat(43);
const commandId = "123e4567-e89b-42d3-a456-426614174000";

class FakeSocket implements BridgeSocket {
    readyState = 0;
    onopen: (() => void) | null = null;
    onmessage: ((event: { data: unknown }) => void) | null = null;
    onclose: ((event: { code: number }) => void) | null = null;
    onerror: (() => void) | null = null;
    sent: string[] = [];

    open(): void {
        this.readyState = 1;
        this.onopen?.();
    }

    receive(value: unknown): void {
        this.onmessage?.({ data: JSON.stringify(value) });
    }

    disconnect(code = 1006): void {
        this.readyState = 3;
        this.onclose?.({ code });
    }

    send(data: string): void {
        this.sent.push(data);
    }

    close(): void {
        this.readyState = 3;
    }
}

function createHarness(secret: string | null = pairingSecret) {
    const sockets: FakeSocket[] = [];
    const snapshots: string[] = [];
    const onNavigate = vi.fn().mockResolvedValue({
        commandId,
        status: "completed",
        method: "history",
    });
    const client = new ExtensionBridgeClient({
        createSocket: () => {
            const socket = new FakeSocket();
            sockets.push(socket);
            return socket;
        },
        getSecret: async () => secret,
        getExtensionVersion: () => "0.1.0",
        onSnapshot: (snapshot) => snapshots.push(snapshot.connection),
        onNavigate,
        random: () => 0,
    });
    return { client, sockets, snapshots, onNavigate };
}

afterEach(() => {
    vi.useRealTimers();
});

describe("ExtensionBridgeClient", () => {
    it("stays unpaired without opening a socket when no secret exists", async () => {
        const { client, sockets } = createHarness(null);
        await client.start();
        expect(sockets).toHaveLength(0);
        expect(client.getSnapshot().connection).toBe("unpaired");
    });

    it("rejects a malformed stored secret without opening a socket", async () => {
        const { client, sockets } = createHarness("not-a-secret");
        await client.start();

        expect(sockets).toHaveLength(0);
        expect(client.getSnapshot().connection).toBe("unpaired");
    });

    it("authenticates, synchronizes mode, and correlates mode results", async () => {
        const { client, sockets } = createHarness();
        await client.start();
        sockets[0]?.open();
        expect(JSON.parse(sockets[0]?.sent[0] ?? "{}")).toMatchObject({
            type: "hello",
            protocolVersion: 1,
            pairingSecret,
        });
        sockets[0]?.receive({
            type: "state",
            protocolVersion: 1,
            mode: "off",
            bridgeStatus: "ready",
        });
        expect(client.getSnapshot().connection).toBe("connected");

        const pending = client.requestMode("current_axiom_tab");
        const request = JSON.parse(sockets[0]?.sent.at(-1) ?? "{}");
        sockets[0]?.receive({
            type: "mode_result",
            protocolVersion: 1,
            requestId: request.requestId,
            accepted: true,
            mode: "current_axiom_tab",
        });
        await expect(pending).resolves.toBe(true);
        expect(client.getSnapshot().mode).toBe("current_axiom_tab");
        client.stop();
    });

    it("reconnects with backoff but stops on pairing rejection", async () => {
        vi.useFakeTimers();
        const { client, sockets } = createHarness();
        await client.start();
        sockets[0]?.disconnect();
        expect(client.getSnapshot()).toMatchObject({
            connection: "reconnecting",
            reconnectAttempt: 1,
        });
        vi.advanceTimersByTime(799);
        expect(sockets).toHaveLength(1);
        vi.advanceTimersByTime(1);
        expect(sockets).toHaveLength(2);
        sockets[1]?.disconnect(4001);
        expect(client.getSnapshot().connection).toBe("pairing_rejected");
        vi.advanceTimersByTime(60_000);
        expect(sockets).toHaveLength(2);
    });

    it("waits for an authenticated state before accepting pairing", async () => {
        const { client, sockets } = createHarness(null);
        await client.start();

        const pairing = client.pair(pairingSecret);
        expect(sockets).toHaveLength(1);
        sockets[0]?.open();
        sockets[0]?.receive({
            type: "state",
            protocolVersion: 1,
            mode: "off",
            bridgeStatus: "ready",
        });

        await expect(pairing).resolves.toBeUndefined();
        client.stop();
    });

    it("rejects pairing when the desktop rejects the secret", async () => {
        const { client, sockets } = createHarness(null);
        await client.start();

        const pairing = client.pair(pairingSecret);
        sockets[0]?.open();
        sockets[0]?.disconnect(4001);

        await expect(pairing).rejects.toThrow("pairing_rejected");
        expect(client.getSnapshot().connection).toBe("pairing_rejected");
    });

    it("does not execute navigation before authentication", async () => {
        const { client, sockets, onNavigate } = createHarness();
        await client.start();
        sockets[0]?.open();
        sockets[0]?.receive({
            type: "navigate",
            protocolVersion: 1,
            commandId,
            url: "https://axiom.trade/meme/pair?chain=sol",
            issuedAt: "2026-09-17T12:00:00.000Z",
        });

        await Promise.resolve();
        expect(onNavigate).not.toHaveBeenCalled();
        client.stop();
    });

    it("returns navigation results to the desktop", async () => {
        const { client, sockets, onNavigate } = createHarness();
        await client.start();
        sockets[0]?.open();
        sockets[0]?.receive({
            type: "state",
            protocolVersion: 1,
            mode: "current_axiom_tab",
            bridgeStatus: "ready",
        });
        sockets[0]?.receive({
            type: "navigate",
            protocolVersion: 1,
            commandId,
            url: "https://axiom.trade/meme/pair?chain=sol",
            issuedAt: "2026-09-17T12:00:00.000Z",
        });
        await vi.waitFor(() => expect(onNavigate).toHaveBeenCalledOnce());
        await vi.waitFor(() =>
            expect(JSON.parse(sockets[0]?.sent.at(-1) ?? "{}")).toMatchObject({
                type: "navigation_result",
                commandId,
                status: "completed",
            }),
        );
        client.stop();
    });
});
