import {
    DEFAULT_FILTERS,
    LAST_TOKEN_FEES_AGE_EXCLUSION_DAYS,
} from "$lib/config/constants.js";

const DAY_IN_MS = 86400000;

export function getLastTokenFeesSummary(
    lastDeployedTokens,
    {
        minFeeThreshold = 0,
        now = Date.now(),
        ageExclusionDays = LAST_TOKEN_FEES_AGE_EXCLUSION_DAYS,
    } = {},
) {
    const consideredFees = [];
    const ageExclusionMs = ageExclusionDays * DAY_IN_MS;

    for (const token of lastDeployedTokens ?? []) {
        const tokenFees = Number(token?.total_pair_fees_paid);
        const normalizedFees = Number.isFinite(tokenFees) ? tokenFees : 0;
        const createdAt = token?.created_at ? new Date(token.created_at) : null;
        const ageInMs = createdAt ? now - createdAt.getTime() : null;
        const shouldExcludeOlderLowFeeToken =
            ageInMs !== null &&
            Number.isFinite(ageInMs) &&
            ageInMs > ageExclusionMs &&
            normalizedFees < minFeeThreshold;

        if (shouldExcludeOlderLowFeeToken) {
            continue;
        }

        consideredFees.push(normalizedFees);
    }

    const totalFees = consideredFees.reduce((sum, fees) => sum + fees, 0);
    const consideredCount = consideredFees.length;
    const averageFees = consideredCount > 0 ? totalFees / consideredCount : 0;

    return {
        consideredCount,
        totalFees,
        averageFees,
        passesFixed:
            consideredCount === 0 ||
            consideredFees.every((fees) => fees >= minFeeThreshold),
    };
}

export function passesLastTokenFeesFilter(
    lastDeployedTokens,
    {
        mode = DEFAULT_FILTERS.feesMode,
        minFeeThreshold = DEFAULT_FILTERS.minLastTokenFees,
        now = Date.now(),
        ageExclusionDays = LAST_TOKEN_FEES_AGE_EXCLUSION_DAYS,
    } = {},
) {
    const summary = getLastTokenFeesSummary(lastDeployedTokens, {
        minFeeThreshold,
        now,
        ageExclusionDays,
    });

    if (summary.consideredCount === 0) {
        return true;
    }

    if (mode === "total") {
        return summary.totalFees >= minFeeThreshold;
    }

    if (mode === "fixed") {
        return summary.passesFixed;
    }

    return summary.averageFees >= minFeeThreshold;
}