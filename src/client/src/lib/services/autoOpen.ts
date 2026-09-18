import {
    extensionBridgeService,
    type ExtensionBridgeService,
} from "$lib/services/extensionBridge";
import { openerService, type UrlOpener } from "$lib/services/opener";
import type { FilterSnapshot, TokenFeed } from "$lib/types";
import { buildAxiomTokenUrl, buildTerminalUrl } from "$lib/utils/tokenLinks";

export interface AutoOpenDispatcher {
    dispatch(feed: TokenFeed, snapshot: FilterSnapshot): void;
}

export class DefaultAutoOpenDispatcher implements AutoOpenDispatcher {
    private readonly currentTabQueue: Array<{
        commandId: string;
        url: string;
        issuedAt: string;
    }> = [];
    private currentTabDispatching = false;

    constructor(
        private readonly opener: UrlOpener = openerService,
        private readonly bridge: ExtensionBridgeService = extensionBridgeService,
    ) {}

    dispatch(feed: TokenFeed, snapshot: FilterSnapshot): void {
        const { autoOpenMode, terminal } = snapshot.filters;
        if (autoOpenMode === "off") return;

        if (autoOpenMode === "new_tab") {
            const url = buildTerminalUrl(feed, terminal);
            if (url) this.run(this.opener.open(url));
            return;
        }

        const url = buildAxiomTokenUrl(feed);
        if (!url) return;
        this.currentTabQueue.push({
            commandId: crypto.randomUUID(),
            url,
            issuedAt: new Date().toISOString(),
        });
        this.dispatchNextCurrentTab();
    }

    private dispatchNextCurrentTab(): void {
        if (this.currentTabDispatching) return;
        const command = this.currentTabQueue.shift();
        if (!command) return;

        this.currentTabDispatching = true;
        let operation: Promise<void>;
        try {
            operation = this.bridge.navigate(command);
        } catch (error: unknown) {
            console.error("Auto-open operation failed:", error);
            this.currentTabDispatching = false;
            this.dispatchNextCurrentTab();
            return;
        }
        operation
            .catch((error: unknown) => {
                console.error("Auto-open operation failed:", error);
            })
            .finally(() => {
                this.currentTabDispatching = false;
                this.dispatchNextCurrentTab();
            });
    }

    private run(operation: Promise<void>): void {
        operation.catch((error: unknown) => {
            console.error("Auto-open operation failed:", error);
        });
    }
}

export const autoOpenDispatcher: AutoOpenDispatcher =
    new DefaultAutoOpenDispatcher();
