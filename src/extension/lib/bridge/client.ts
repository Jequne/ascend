import type { NavigationResult } from "../types/navigation";
import {
    BRIDGE_PROTOCOL_VERSION,
    BRIDGE_URL,
    type ExtensionBridgeMessage,
    type ExtensionBridgeSnapshot,
} from "../types/bridge";
import { parseDesktopBridgeMessage } from "./protocol";

const HEARTBEAT_INTERVAL_MS = 20_000;
const MODE_RESULT_TIMEOUT_MS = 5_000;
const PAIRING_TIMEOUT_MS = 6_000;
const MAX_RECONNECT_DELAY_MS = 30_000;

export interface BridgeSocket {
    readonly readyState: number;
    onopen: (() => void) | null;
    onmessage: ((event: { data: unknown }) => void) | null;
    onclose: ((event: { code: number }) => void) | null;
    onerror: (() => void) | null;
    send(data: string): void;
    close(): void;
}

type PendingMode = {
    expected: "off" | "current_axiom_tab";
    resolve: (accepted: boolean) => void;
    timeout: ReturnType<typeof setTimeout>;
};

type PairingWaiter = {
    resolve: () => void;
    reject: (error: Error) => void;
    timeout: ReturnType<typeof setTimeout>;
};

export type BridgeClientDependencies = {
    createSocket?: (url: string) => BridgeSocket;
    getSecret: () => Promise<string | null>;
    getExtensionVersion: () => string;
    onSnapshot: (snapshot: ExtensionBridgeSnapshot) => void;
    onNavigate: (command: {
        commandId: string;
        url: string;
        issuedAt: string;
    }) => Promise<NavigationResult>;
    random?: () => number;
};

export class ExtensionBridgeClient {
    private socket: BridgeSocket | null = null;
    private secret: string | null = null;
    private stopped = true;
    private authenticated = false;
    private reconnectAttempt = 0;
    private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
    private pendingModes = new Map<string, PendingMode>();
    private pairingWaiters = new Set<PairingWaiter>();
    private snapshot: ExtensionBridgeSnapshot = {
        connection: "unpaired",
        mode: "off",
        reconnectAttempt: 0,
    };

    constructor(private readonly dependencies: BridgeClientDependencies) {}

    async start(): Promise<void> {
        this.stopped = false;
        this.secret = await this.dependencies.getSecret();
        if (!this.secret || !isPairingSecret(this.secret)) {
            this.secret = null;
            this.updateSnapshot({
                connection: "unpaired",
                reconnectAttempt: 0,
            });
            return;
        }
        this.connect(false);
    }

    stop(): void {
        this.stopped = true;
        this.clearTimers();
        this.rejectPendingModes();
        this.rejectPairingWaiters("bridge_stopped");
        this.socket?.close();
        this.socket = null;
        this.authenticated = false;
    }

    async pair(secret: string): Promise<void> {
        const normalized = secret.trim();
        if (!isPairingSecret(normalized))
            throw new Error("invalid_pairing_code");
        this.secret = normalized;
        this.stopped = false;
        this.reconnectAttempt = 0;
        this.clearTimers();
        this.socket?.close();
        this.socket = null;
        this.connect(false);
        try {
            await this.waitForPairing();
        } catch (error: unknown) {
            if (
                this.snapshot.connection === "connecting" ||
                this.snapshot.connection === "reconnecting"
            ) {
                this.stopped = true;
                this.clearTimers();
                this.closeSocket();
                this.updateSnapshot({ connection: "unavailable" });
            }
            throw error;
        }
    }

    retry(): void {
        if (!this.secret || this.snapshot.connection === "connected") return;
        this.stopped = false;
        this.reconnectAttempt = 0;
        this.clearTimers();
        this.socket?.close();
        this.socket = null;
        this.connect(false);
    }

    getSnapshot(): ExtensionBridgeSnapshot {
        return { ...this.snapshot };
    }

    requestMode(mode: "off" | "current_axiom_tab"): Promise<boolean> {
        if (
            !this.authenticated ||
            !this.socket ||
            this.socket.readyState !== 1
        ) {
            return Promise.resolve(false);
        }
        const requestId = crypto.randomUUID();
        return new Promise<boolean>((resolve) => {
            const timeout = setTimeout(() => {
                this.pendingModes.delete(requestId);
                resolve(false);
            }, MODE_RESULT_TIMEOUT_MS);
            this.pendingModes.set(requestId, {
                expected: mode,
                resolve,
                timeout,
            });
            this.send({
                type: "set_mode",
                protocolVersion: BRIDGE_PROTOCOL_VERSION,
                requestId,
                mode,
            });
        });
    }

    private connect(isReconnect: boolean): void {
        if (this.stopped || !this.secret || this.socket) return;
        this.authenticated = false;
        this.updateSnapshot({
            connection: isReconnect ? "reconnecting" : "connecting",
            reconnectAttempt: this.reconnectAttempt,
        });

        const createSocket =
            this.dependencies.createSocket ??
            ((url: string) => new WebSocket(url) as BridgeSocket);
        try {
            const socket = createSocket(BRIDGE_URL);
            this.socket = socket;
            socket.onopen = () => {
                if (this.socket !== socket || !this.secret) return;
                this.send({
                    type: "hello",
                    protocolVersion: BRIDGE_PROTOCOL_VERSION,
                    extensionVersion: this.dependencies.getExtensionVersion(),
                    pairingSecret: this.secret,
                });
            };
            socket.onmessage = (event) => {
                if (this.socket === socket) void this.handleMessage(event.data);
            };
            socket.onerror = () => undefined;
            socket.onclose = (event) => {
                if (this.socket !== socket) return;
                this.socket = null;
                this.authenticated = false;
                this.stopHeartbeat();
                this.rejectPendingModes();
                if (event.code === 4001) {
                    this.stopped = true;
                    this.updateSnapshot({ connection: "pairing_rejected" });
                    this.rejectPairingWaiters("pairing_rejected");
                } else if (event.code === 4002 || event.code === 4003) {
                    this.stopped = true;
                    this.updateSnapshot({ connection: "version_mismatch" });
                    this.rejectPairingWaiters("version_mismatch");
                } else {
                    this.scheduleReconnect();
                }
            };
        } catch {
            this.socket = null;
            this.scheduleReconnect();
        }
    }

    private async handleMessage(raw: unknown): Promise<void> {
        const message = parseDesktopBridgeMessage(raw);
        if (!message) return;

        if (message.type === "state") {
            this.authenticated = true;
            this.reconnectAttempt = 0;
            this.updateSnapshot({
                connection: "connected",
                mode: message.mode,
                reconnectAttempt: 0,
            });
            this.startHeartbeat();
            this.resolvePairingWaiters();
            for (const [requestId, pending] of this.pendingModes) {
                if (pending.expected === message.mode) {
                    clearTimeout(pending.timeout);
                    pending.resolve(true);
                    this.pendingModes.delete(requestId);
                }
            }
            return;
        }
        if (!this.authenticated) return;
        if (message.type === "mode_result") {
            const pending = this.pendingModes.get(message.requestId);
            if (pending) {
                clearTimeout(pending.timeout);
                pending.resolve(
                    message.accepted && pending.expected === message.mode,
                );
                this.pendingModes.delete(message.requestId);
            }
            if (message.accepted) this.updateSnapshot({ mode: message.mode });
            return;
        }
        if (message.type === "navigate") {
            const result = await this.dependencies.onNavigate(message);
            this.send({
                type: "navigation_result",
                protocolVersion: BRIDGE_PROTOCOL_VERSION,
                ...result,
            });
        }
    }

    private send(message: ExtensionBridgeMessage): void {
        if (!this.socket || this.socket.readyState !== 1) return;
        this.socket.send(JSON.stringify(message));
    }

    private startHeartbeat(): void {
        this.stopHeartbeat();
        this.heartbeatTimer = setInterval(() => {
            this.send({
                type: "ping",
                protocolVersion: BRIDGE_PROTOCOL_VERSION,
                sentAt: new Date().toISOString(),
            });
        }, HEARTBEAT_INTERVAL_MS);
    }

    private stopHeartbeat(): void {
        if (this.heartbeatTimer) clearInterval(this.heartbeatTimer);
        this.heartbeatTimer = null;
    }

    private scheduleReconnect(): void {
        if (this.stopped || !this.secret || this.reconnectTimer) return;
        this.reconnectAttempt += 1;
        const random = this.dependencies.random ?? Math.random;
        const baseDelay = Math.min(
            MAX_RECONNECT_DELAY_MS,
            1000 * 2 ** Math.min(this.reconnectAttempt - 1, 5),
        );
        const delay = Math.round(baseDelay * (0.8 + random() * 0.4));
        this.updateSnapshot({
            connection: "reconnecting",
            reconnectAttempt: this.reconnectAttempt,
        });
        this.reconnectTimer = setTimeout(() => {
            this.reconnectTimer = null;
            this.connect(true);
        }, delay);
    }

    private rejectPendingModes(): void {
        for (const pending of this.pendingModes.values()) {
            clearTimeout(pending.timeout);
            pending.resolve(false);
        }
        this.pendingModes.clear();
    }

    private waitForPairing(): Promise<void> {
        if (this.authenticated) return Promise.resolve();
        return new Promise<void>((resolve, reject) => {
            const waiter: PairingWaiter = {
                resolve,
                reject,
                timeout: setTimeout(() => {
                    this.pairingWaiters.delete(waiter);
                    reject(new Error("pairing_timeout"));
                }, PAIRING_TIMEOUT_MS),
            };
            this.pairingWaiters.add(waiter);
        });
    }

    private resolvePairingWaiters(): void {
        for (const waiter of this.pairingWaiters) {
            clearTimeout(waiter.timeout);
            waiter.resolve();
        }
        this.pairingWaiters.clear();
    }

    private rejectPairingWaiters(code: string): void {
        for (const waiter of this.pairingWaiters) {
            clearTimeout(waiter.timeout);
            waiter.reject(new Error(code));
        }
        this.pairingWaiters.clear();
    }

    private clearTimers(): void {
        if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
        this.reconnectTimer = null;
        this.stopHeartbeat();
    }

    private closeSocket(): void {
        this.socket?.close();
        this.socket = null;
    }

    private updateSnapshot(partial: Partial<ExtensionBridgeSnapshot>): void {
        this.snapshot = { ...this.snapshot, ...partial };
        this.dependencies.onSnapshot({ ...this.snapshot });
    }
}

export function isPairingSecret(value: string): boolean {
    return /^[A-Za-z0-9_-]{43}$/.test(value);
}
