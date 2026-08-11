import type { TokenFeed } from "$lib/types";

export const TOKEN_FEED_LIMIT = 30;

export function prependRollingFeed(
    feeds: readonly TokenFeed[],
    nextFeed: TokenFeed,
    limit = TOKEN_FEED_LIMIT,
): TokenFeed[] {
    return [nextFeed, ...feeds].slice(0, Math.max(0, limit));
}
