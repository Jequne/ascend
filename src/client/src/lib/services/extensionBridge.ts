import { invoke } from "@tauri-apps/api/core";
import type { AutoOpenMode } from "$lib/types";

export type BridgeListenerStatus =
    "starting" | "ready" | "port_in_use" | "unavailable";
export type BridgeConnectionStatus = "disconnected" | "connected";

export type ExtensionBridgeState = {
    listenerStatus: BridgeListenerStatus;
    connectionStatus: BridgeConnectionStatus;
    targetStatus: "selected" | "missing";
    mode: AutoOpenMode;
};

export interface ExtensionBridgeService {
    getState(): Promise<ExtensionBridgeState>;
    getPairingCode(): Promise<string>;
    rotatePairingCode(): Promise<string>;
    setMode(mode: AutoOpenMode): Promise<void>;
    navigate(command: {
        commandId: string;
        url: string;
        issuedAt: string;
    }): Promise<void>;
}

class TauriExtensionBridgeService implements ExtensionBridgeService {
    async getState(): Promise<ExtensionBridgeState> {
        const value: unknown = await invoke("get_extension_bridge_state");
        if (!isExtensionBridgeState(value))
            throw new Error("invalid_bridge_state");
        return value;
    }

    getPairingCode(): Promise<string> {
        return invoke<string>("get_extension_pairing_code");
    }

    rotatePairingCode(): Promise<string> {
        return invoke<string>("rotate_extension_pairing_code");
    }

    setMode(mode: AutoOpenMode): Promise<void> {
        return invoke("set_extension_auto_open_mode", { mode });
    }

    navigate(command: {
        commandId: string;
        url: string;
        issuedAt: string;
    }): Promise<void> {
        return invoke("send_extension_navigation", command);
    }
}

export function isExtensionBridgeState(
    value: unknown,
): value is ExtensionBridgeState {
    if (typeof value !== "object" || value === null || Array.isArray(value)) {
        return false;
    }
    const state = value as Record<string, unknown>;
    return (
        (state.listenerStatus === "starting" ||
            state.listenerStatus === "ready" ||
            state.listenerStatus === "port_in_use" ||
            state.listenerStatus === "unavailable") &&
        (state.connectionStatus === "disconnected" ||
            state.connectionStatus === "connected") &&
        (state.targetStatus === "selected" ||
            state.targetStatus === "missing") &&
        (state.mode === "off" ||
            state.mode === "new_tab" ||
            state.mode === "current_axiom_tab")
    );
}

export const extensionBridgeService: ExtensionBridgeService =
    new TauriExtensionBridgeService();
