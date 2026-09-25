import {
    DEFAULT_FILTERS,
    LAST_TOKEN_FEES_AGE_EXCLUSION_DAYS,
} from "$lib/config/constants";
import type { FeesMode, LastDeployedToken } from "$lib/types";

const DAY_IN_MS = 86_400_000;

interface LastTokenFeesOptions {
    minFeeThreshold?: number;
    now?: number;
    ageExclusionDays?: number;
}

interface LastTokenFeesFilterOptions extends LastTokenFeesOptions {
    mode?: FeesMode;
}

export interface LastTokenFeesSummary {
    consideredCount: number;
    totalFees: number;
    averageFees: number;
    passesFixed: boolean;
}

function isVerifiedFee(value: number | null): value is number {
    return typeof value === "number" && Number.isFinite(value) && value >= 0;
}

export function getLastTokenFeesSummary(
    lastDeployedTokens: readonly LastDeployedToken[] | null | undefined,
    {
        minFeeThreshold = 0,
        now = Date.now(),
        ageExclusionDays = LAST_TOKEN_FEES_AGE_EXCLUSION_DAYS,
    }: LastTokenFeesOptions = {},
): LastTokenFeesSummary {
    const consideredFees: number[] = [];
    const ageExclusionMs = ageExclusionDays * DAY_IN_MS;

    for (const token of lastDeployedTokens ?? []) {
        const tokenFees = token.total_pair_fees_paid;
        if (!isVerifiedFee(tokenFees)) continue;
        const createdAt = token.created_at ? new Date(token.created_at) : null;
        const ageInMs = createdAt ? now - createdAt.getTime() : null;
        const shouldExcludeOlderLowFeeToken =
            ageInMs !== null &&
            Number.isFinite(ageInMs) &&
            ageInMs > ageExclusionMs &&
            tokenFees < minFeeThreshold;

        if (!shouldExcludeOlderLowFeeToken) consideredFees.push(tokenFees);
    }

    const totalFees = consideredFees.reduce((sum, fees) => sum + fees, 0);
    const consideredCount = consideredFees.length;

    return {
        consideredCount,
        totalFees,
        averageFees: consideredCount > 0 ? totalFees / consideredCount : 0,
        passesFixed:
            consideredCount === 0 ||
            consideredFees.every((fees) => fees >= minFeeThreshold),
    };
}

export function passesLastTokenFeesFilter(
    lastDeployedTokens: readonly LastDeployedToken[] | null | undefined,
    {
        mode = DEFAULT_FILTERS.feesMode,
        minFeeThreshold = DEFAULT_FILTERS.minLastTokenFees,
        now = Date.now(),
        ageExclusionDays = LAST_TOKEN_FEES_AGE_EXCLUSION_DAYS,
    }: LastTokenFeesFilterOptions = {},
): boolean {
    if (
        (lastDeployedTokens ?? []).some(
            (token) => !isVerifiedFee(token.total_pair_fees_paid),
        )
    )
        return false;
    const summary = getLastTokenFeesSummary(lastDeployedTokens, {
        minFeeThreshold,
        now,
        ageExclusionDays,
    });

    if (summary.consideredCount === 0) return true;
    if (mode === "total") return summary.totalFees >= minFeeThreshold;
    if (mode === "fixed") return summary.passesFixed;
    return summary.averageFees >= minFeeThreshold;
}
