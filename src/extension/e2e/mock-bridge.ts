import { once } from "node:events";
import WebSocket, { WebSocketServer } from "ws";

export const E2E_PAIRING_CODE = "e".repeat(43);

type NavigationResult = {
    commandId: string;
    status: "completed" | "superseded" | "ignored" | "failed";
    method?: "history";
    errorCode?: string;
};

type PendingNavigation = {
    resolve: (result: NavigationResult) => void;
    reject: (error: Error) => void;
    timeout: ReturnType<typeof setTimeout>;
};

export class MockBridge {
    private readonly server: WebSocketServer;
    private socket: WebSocket | null = null;
    private mode: "off" | "current_axiom_tab" = "off";
    private modeRequestCount = 0;
    private readonly pending = new Map<string, PendingNavigation>();

    private constructor(extensionId: string) {
        this.server = new WebSocketServer({
            host: "127.0.0.1",
            port: 17_321,
            path: "/extension/v1",
            verifyClient: ({ origin }: { origin: string }) =>
                origin === `chrome-extension://${extensionId}`,
        });
        this.server.on("connection", (socket) => this.handleConnection(socket));
    }

    static async start(extensionId: string): Promise<MockBridge> {
        const bridge = new MockBridge(extensionId);
        await once(bridge.server, "listening");
        return bridge;
    }

    async navigate(
        commandId: string,
        url: string,
        issuedAt: string,
    ): Promise<NavigationResult> {
        if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
            throw new Error("mock_bridge_not_connected");
        }
        const result = new Promise<NavigationResult>((resolve, reject) => {
            const timeout = setTimeout(() => {
                this.pending.delete(commandId);
                reject(new Error("mock_navigation_timeout"));
            }, 10_000);
            this.pending.set(commandId, { resolve, reject, timeout });
        });
        this.socket.send(
            JSON.stringify({
                type: "navigate",
                protocolVersion: 1,
                commandId,
                url,
                issuedAt,
            }),
        );
        return result;
    }

    send(message: unknown): void {
        if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
            throw new Error("mock_bridge_not_connected");
        }
        this.socket.send(JSON.stringify(message));
    }

    disconnect(code = 1012, reason = "test_disconnect"): void {
        if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
            throw new Error("mock_bridge_not_connected");
        }
        this.socket.close(code, reason);
    }

    getModeRequestCount(): number {
        return this.modeRequestCount;
    }

    async close(): Promise<void> {
        for (const pending of this.pending.values()) {
            clearTimeout(pending.timeout);
            pending.reject(new Error("mock_bridge_closed"));
        }
        this.pending.clear();
        for (const client of this.server.clients) client.terminate();
        await new Promise<void>((resolve, reject) => {
            this.server.close((error) => (error ? reject(error) : resolve()));
        });
    }

    private handleConnection(socket: WebSocket): void {
        this.socket?.close(4004, "replaced");
        this.socket = socket;
        let authenticated = false;

        socket.on("message", (data, isBinary) => {
            if (isBinary) {
                socket.close(4000, "invalid_message");
                return;
            }
            const message = parseRecord(data.toString());
            if (!message) {
                socket.close(4000, "invalid_message");
                return;
            }
            if (!authenticated) {
                if (
                    message.type !== "hello" ||
                    message.protocolVersion !== 1 ||
                    message.pairingSecret !== E2E_PAIRING_CODE
                ) {
                    socket.close(4001, "pairing_rejected");
                    return;
                }
                authenticated = true;
                socket.send(
                    JSON.stringify({
                        type: "state",
                        protocolVersion: 1,
                        mode: this.mode,
                        bridgeStatus: "ready",
                    }),
                );
                return;
            }

            if (
                message.type === "set_mode" &&
                typeof message.requestId === "string" &&
                (message.mode === "off" || message.mode === "current_axiom_tab")
            ) {
                this.mode = message.mode;
                this.modeRequestCount += 1;
                socket.send(
                    JSON.stringify({
                        type: "mode_result",
                        protocolVersion: 1,
                        requestId: message.requestId,
                        accepted: true,
                        mode: this.mode,
                    }),
                );
                return;
            }
            if (message.type === "ping" && typeof message.sentAt === "string") {
                socket.send(
                    JSON.stringify({
                        type: "pong",
                        protocolVersion: 1,
                        sentAt: message.sentAt,
                    }),
                );
                return;
            }
            if (
                message.type === "navigation_result" &&
                typeof message.commandId === "string" &&
                isNavigationStatus(message.status)
            ) {
                const pending = this.pending.get(message.commandId);
                if (!pending) return;
                clearTimeout(pending.timeout);
                this.pending.delete(message.commandId);
                pending.resolve({
                    commandId: message.commandId,
                    status: message.status,
                    ...(message.method === "history"
                        ? { method: message.method }
                        : {}),
                    ...(typeof message.errorCode === "string"
                        ? { errorCode: message.errorCode }
                        : {}),
                });
            }
        });
        socket.on("close", () => {
            if (this.socket === socket) this.socket = null;
        });
        socket.on("error", () => undefined);
    }
}

function parseRecord(value: string): Record<string, unknown> | null {
    try {
        const parsed: unknown = JSON.parse(value);
        return typeof parsed === "object" &&
            parsed !== null &&
            !Array.isArray(parsed)
            ? (parsed as Record<string, unknown>)
            : null;
    } catch {
        return null;
    }
}

function isNavigationStatus(
    value: unknown,
): value is NavigationResult["status"] {
    return (
        value === "completed" ||
        value === "superseded" ||
        value === "ignored" ||
        value === "failed"
    );
}
