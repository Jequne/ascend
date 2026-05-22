import { DEFAULT_FILTERS } from "$lib/config/constants.js";

const MAX_LAST_TOKENS = 3;

export function passesLastTokensFilter(
    lastDeployedTokens,
    {
        minAthMcapThreshold = DEFAULT_FILTERS.minLastTokenAthMcap,
        requiredCount = DEFAULT_FILTERS.lastTokensRequiredCount,
        maxTokens = MAX_LAST_TOKENS,
    } = {},
) {
    const normalizedRequiredCount = Math.max(0, Math.min(MAX_LAST_TOKENS, Math.round(Number(requiredCount))));

    if (normalizedRequiredCount === 0) {
        return false;
    }

    const normalizedThreshold = Math.max(0, Number(minAthMcapThreshold));
    const qualifyingCount = (lastDeployedTokens ?? [])
        .slice(0, Math.max(0, Math.min(MAX_LAST_TOKENS, Math.round(Number(maxTokens)))))
        .filter((token) => {
            const athMcap = Number(token?.ath_mcap_in_usd);
            return Number.isFinite(athMcap) && athMcap >= normalizedThreshold;
        }).length;

    return qualifyingCount >= normalizedRequiredCount;
}