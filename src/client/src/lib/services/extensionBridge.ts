import { invoke } from "@tauri-apps/api/core";
import type { AutoOpenMode } from "$lib/types";

export type BridgeListenerStatus =
    "starting" | "ready" | "port_in_use" | "unavailable";
export type BridgeConnectionStatus =
    "disconnected" | "connected" | "pairing_rejected" | "version_mismatch";

export type ExtensionInstallationInfo = {
    path: string;
    version: string;
};

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
    prepareInstallation(): Promise<ExtensionInstallationInfo>;
    openInstallationFolder(): Promise<ExtensionInstallationInfo>;
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

    async prepareInstallation(): Promise<ExtensionInstallationInfo> {
        const value: unknown = await invoke("prepare_extension_installation");
        if (!isExtensionInstallationInfo(value)) {
            throw new Error("invalid_extension_installation_info");
        }
        return value;
    }

    async openInstallationFolder(): Promise<ExtensionInstallationInfo> {
        const value: unknown = await invoke(
            "open_extension_installation_folder",
        );
        if (!isExtensionInstallationInfo(value)) {
            throw new Error("invalid_extension_installation_info");
        }
        return value;
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
            state.connectionStatus === "connected" ||
            state.connectionStatus === "pairing_rejected" ||
            state.connectionStatus === "version_mismatch") &&
        (state.targetStatus === "selected" ||
            state.targetStatus === "missing") &&
        (state.mode === "off" ||
            state.mode === "new_tab" ||
            state.mode === "current_axiom_tab")
    );
}

export function isExtensionInstallationInfo(
    value: unknown,
): value is ExtensionInstallationInfo {
    if (typeof value !== "object" || value === null || Array.isArray(value)) {
        return false;
    }
    const info = value as Record<string, unknown>;
    return (
        typeof info.path === "string" &&
        info.path.length > 0 &&
        typeof info.version === "string" &&
        /^\d+\.\d+\.\d+$/.test(info.version)
    );
}

export const extensionBridgeService: ExtensionBridgeService =
    new TauriExtensionBridgeService();
