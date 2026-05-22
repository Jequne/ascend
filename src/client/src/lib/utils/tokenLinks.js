import { openUrl } from "@tauri-apps/plugin-opener";

export function buildTerminalUrl(token, terminal) {
    const blockchain = token?.blockchain || "sol";

    if (terminal === "gmgn") {
        return `https://gmgn.ai/${blockchain}/token/${token?.token_address}`;
    }

    return `https://axiom.trade/meme/${token?.pair_address}?chain=${blockchain}`;
}

export async function openTokenUrlInNewTab(token, terminal) {
    const url = buildTerminalUrl(token, terminal);

    if (!url) return;

    const openedWindow =
        typeof window !== "undefined"
            ? window.open(url, "_blank", "noopener,noreferrer")
            : null;

    if (openedWindow) return;

    try {
        await openUrl(url);
    } catch (error) {
        console.error("Failed to open token URL:", error);
    }
}