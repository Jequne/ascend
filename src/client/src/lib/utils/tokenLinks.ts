import { openUrl } from "@tauri-apps/plugin-opener";
import type {
    LastDeployedToken,
    Terminal,
    TokenFeed,
    TokenFeedPayload,
} from "$lib/types";

type LinkableToken = TokenFeed | TokenFeedPayload | LastDeployedToken;

export function buildTerminalUrl(
    token: LinkableToken,
    terminal: Terminal,
): string {
    const blockchain = token.blockchain || "sol";

    if (terminal === "gmgn") {
        return `https://gmgn.ai/${blockchain}/token/${token.token_address}`;
    }

    return `https://axiom.trade/meme/${token.pair_address}?chain=${blockchain}`;
}

export async function openTokenUrlInNewTab(
    token: LinkableToken,
    terminal: Terminal,
): Promise<void> {
    const url = buildTerminalUrl(token, terminal);
    const openedWindow = window.open(url, "_blank", "noopener,noreferrer");

    if (openedWindow) return;

    try {
        await openUrl(url);
    } catch (error: unknown) {
        console.error("Failed to open token URL:", error);
    }
}
