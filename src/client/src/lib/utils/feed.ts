import type {
    FeedDecision,
    FilterSnapshot,
    TokenFeed,
    TokenFeedPayload,
} from "$lib/types";
import { tokenMatchesBlacklist } from "$lib/utils/blacklist";
import { passesDevFundingStrategy } from "$lib/utils/devFunding";
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

    const devFeesPass = passesLastTokenFeesFilter(
        payload.last_deployed_tokens,
        {
            mode: filters.feesMode,
            minFeeThreshold: filters.minLastTokenFees,
        },
    );

    const allTokens = payload.all_tokens_count || 0;
    const migratedTokens = payload.migrated_tokens_count || 0;
    const migrationPercent =
        allTokens > 0 ? (migratedTokens / allTokens) * 100 : 0;

    const devMigrationsPass =
        payload.last_deployed_tokens !== null &&
        devFeesPass &&
        migrationPercent >= filters.minMigrationPercent;
    const devFundingPass = passesDevFundingStrategy(payload, filters);
    if (!devMigrationsPass && !devFundingPass && !lastTokensPass) {
        return {
            accepted: false,
            feed: null,
            reason: devFeesPass ? "migration" : "fees",
        };
    }

    return {
        accepted: true,
        reason: null,
        feed: {
            ...payload,
            clientKey,
            indicators: [
                ...(devMigrationsPass ? ["Dev Migrations"] : []),
                ...(devFundingPass ? ["Dev Funding"] : []),
                ...(lastTokensPass ? ["last tokens"] : []),
            ],
            last_deployed_tokens: payload.last_deployed_tokens ?? [],
            funding_wallet: payload.funding_wallet ?? null,
            funding_deployed_tokens: payload.funding_deployed_tokens ?? [],
        },
    };
}
