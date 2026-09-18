import { listen, type UnlistenFn } from "@tauri-apps/api/event";
import {
    extensionBridgeService,
    isExtensionBridgeState,
    type ExtensionBridgeService,
    type ExtensionBridgeState,
} from "$lib/services/extensionBridge";
import { filtersStore } from "$lib/stores/filters.svelte";
import type { AutoOpenMode } from "$lib/types";

type ModeChangedEvent = { mode: AutoOpenMode };

class ExtensionBridgeStore {
    state = $state<ExtensionBridgeState>({
        listenerStatus: "starting",
        connectionStatus: "disconnected",
        targetStatus: "missing",
        mode: "off",
    });
    isInitialized = $state(false);
    private unlistenState: UnlistenFn | null = null;
    private unlistenMode: UnlistenFn | null = null;

    constructor(
        private readonly service: ExtensionBridgeService = extensionBridgeService,
    ) {}

    async init(): Promise<void> {
        if (this.isInitialized) return;
        this.isInitialized = true;
        try {
            this.unlistenState = await listen<unknown>(
                "ascend://bridge-state",
                (event) => {
                    if (isExtensionBridgeState(event.payload)) {
                        this.state = event.payload;
                    }
                },
            );
            this.unlistenMode = await listen<unknown>(
                "ascend://extension-mode-changed",
                (event) => {
                    if (!isModeChangedEvent(event.payload)) return;
                    filtersStore.autoOpenMode = event.payload.mode;
                    this.state = { ...this.state, mode: event.payload.mode };
                },
            );
            this.state = await this.service.getState();
            await this.setMode(filtersStore.autoOpenMode);
        } catch {
            this.state = {
                ...this.state,
                listenerStatus: "unavailable",
                connectionStatus: "disconnected",
            };
        }
    }

    async setMode(mode: AutoOpenMode): Promise<void> {
        this.state = { ...this.state, mode };
        try {
            await this.service.setMode(mode);
        } catch {
            this.state = { ...this.state, listenerStatus: "unavailable" };
        }
    }

    destroy(): void {
        this.unlistenState?.();
        this.unlistenMode?.();
        this.unlistenState = null;
        this.unlistenMode = null;
        this.isInitialized = false;
    }
}

function isModeChangedEvent(value: unknown): value is ModeChangedEvent {
    if (typeof value !== "object" || value === null || Array.isArray(value)) {
        return false;
    }
    const mode = (value as Record<string, unknown>).mode;
    return mode === "off" || mode === "current_axiom_tab";
}

export const extensionBridgeStore = new ExtensionBridgeStore();
