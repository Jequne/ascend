import type {
    LastDeployedToken,
    Terminal,
    TokenFeed,
    TokenFeedPayload,
} from "$lib/types";

type LinkableToken = TokenFeed | TokenFeedPayload | LastDeployedToken;

export function normalizeExternalUrl(value: unknown): string | null {
    if (typeof value !== "string" || !value.trim()) return null;

    try {
        const url = new URL(value);
        return url.protocol === "https:" || url.protocol === "http:"
            ? url.toString()
            : null;
    } catch {
        return null;
    }
}

export function buildTerminalUrl(
    token: LinkableToken,
    terminal: Terminal,
): string | null {
    const blockchain = token.blockchain || "sol";

    if (terminal === "gmgn") {
        if (!token.token_address.trim()) return null;
        return normalizeExternalUrl(
            `https://gmgn.ai/${blockchain}/token/${token.token_address}`,
        );
    }

    if (!token.pair_address.trim()) return null;
    return normalizeExternalUrl(
        `https://axiom.trade/meme/${token.pair_address}?chain=${blockchain}`,
    );
}
