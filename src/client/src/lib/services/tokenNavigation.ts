import {
    extensionBridgeService,
    type ExtensionBridgeService,
} from "$lib/services/extensionBridge";
import { openerService, type UrlOpener } from "$lib/services/opener";
import type {
    AutoOpenMode,
    LastDeployedToken,
    Terminal,
    TokenFeed,
} from "$lib/types";
import { buildAxiomTokenUrl, buildTerminalUrl } from "$lib/utils/tokenLinks";

type NavigableToken = TokenFeed | LastDeployedToken;

export class TokenNavigationService {
    constructor(
        private readonly opener: UrlOpener = openerService,
        private readonly bridge: ExtensionBridgeService = extensionBridgeService,
    ) {}

    open(
        token: NavigableToken,
        terminal: Terminal,
        autoOpenMode: AutoOpenMode,
    ): void {
        if (autoOpenMode === "current_axiom_tab") {
            const url = buildAxiomTokenUrl(token);
            if (!url) return;
            this.run(
                this.bridge.navigate({
                    commandId: crypto.randomUUID(),
                    url,
                    issuedAt: new Date().toISOString(),
                }),
            );
            return;
        }

        const url = buildTerminalUrl(token, terminal);
        if (url) this.run(this.opener.open(url));
    }

    private run(operation: Promise<void>): void {
        operation.catch((error: unknown) => {
            console.error("Token navigation failed:", error);
        });
    }
}

export const tokenNavigationService = new TokenNavigationService();
