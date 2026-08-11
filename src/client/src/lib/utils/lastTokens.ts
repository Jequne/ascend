import { DEFAULT_FILTERS } from "$lib/config/constants";
import type { LastDeployedToken } from "$lib/types";

const MAX_LAST_TOKENS = 3;

interface LastTokensFilterOptions {
    minAthMcapThreshold?: number;
    requiredCount?: number;
    maxTokens?: number;
}

export function passesLastTokensFilter(
    lastDeployedTokens: readonly LastDeployedToken[] | null | undefined,
    {
        minAthMcapThreshold = DEFAULT_FILTERS.minLastTokenAthMcap,
        requiredCount = DEFAULT_FILTERS.lastTokensRequiredCount,
        maxTokens = MAX_LAST_TOKENS,
    }: LastTokensFilterOptions = {},
): boolean {
    const normalizedRequiredCount = Math.max(
        0,
        Math.min(MAX_LAST_TOKENS, Math.round(requiredCount)),
    );

    if (normalizedRequiredCount === 0) return false;

    const normalizedThreshold = Math.max(0, minAthMcapThreshold);
    const normalizedMaxTokens = Math.max(
        0,
        Math.min(MAX_LAST_TOKENS, Math.round(maxTokens)),
    );
    const qualifyingCount = (lastDeployedTokens ?? [])
        .slice(0, normalizedMaxTokens)
        .filter((token) => {
            const athMcap = Number(token.ath_mcap_in_usd);
            return Number.isFinite(athMcap) && athMcap >= normalizedThreshold;
        }).length;

    return qualifyingCount >= normalizedRequiredCount;
}
