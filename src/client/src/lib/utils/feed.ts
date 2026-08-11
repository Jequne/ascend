import type {
    FeedDecision,
    FilterSnapshot,
    TokenFeed,
    TokenFeedPayload,
} from "$lib/types";
import { tokenMatchesBlacklist } from "$lib/utils/blacklist";
import { passesLastTokenFeesFilter } from "$lib/utils/lastTokenFees";
import { passesLastTokensFilter } from "$lib/utils/lastTokens";

export const TOKEN_FEED_LIMIT = 30;

export function prependRollingFeed(
    feeds: readonly TokenFeed[],
    nextFeed: TokenFeed,
    limit = TOKEN_FEED_LIMIT,
): TokenFeed[] {
    return [nextFeed, ...feeds].slice(0, Math.max(0, limit));
}

export function evaluateTokenFeed(
    payload: TokenFeedPayload,
    snapshot: FilterSnapshot,
    clientKey: string,
): FeedDecision {
    const { filters, blacklistMatcher } = snapshot;
    const lastTokensPass = passesLastTokensFilter(
        payload.last_deployed_tokens,
        {
            minAthMcapThreshold: filters.minLastTokenAthMcap,
            requiredCount: filters.lastTokensRequiredCount,
        },
    );

    if (tokenMatchesBlacklist(payload, blacklistMatcher)) {
        return { accepted: false, feed: null, reason: "blacklist" };
    }

    if (
        payload.dev_holds_percent === null ||
        payload.dev_holds_percent < filters.minDevHoldsPercent ||
        payload.dev_holds_percent > filters.maxDevHoldsPercent
    ) {
        return { accepted: false, feed: null, reason: "dev-holds" };
    }

    if (
        !passesLastTokenFeesFilter(payload.last_deployed_tokens, {
            mode: filters.feesMode,
            minFeeThreshold: filters.minLastTokenFees,
        })
    ) {
        return { accepted: false, feed: null, reason: "fees" };
    }

    const allTokens = payload.all_tokens_count || 0;
    const migratedTokens = payload.migrated_tokens_count || 0;
    const migrationPercent =
        allTokens > 0 ? (migratedTokens / allTokens) * 100 : 0;

    if (migrationPercent < filters.minMigrationPercent && !lastTokensPass) {
        return { accepted: false, feed: null, reason: "migration" };
    }

    return {
        accepted: true,
        reason: null,
        feed: {
            ...payload,
            clientKey,
            indicators: [
                ...(payload.indicator ? [payload.indicator] : []),
                ...(lastTokensPass ? ["last tokens"] : []),
            ],
            last_deployed_tokens: payload.last_deployed_tokens ?? [],
        },
    };
}
