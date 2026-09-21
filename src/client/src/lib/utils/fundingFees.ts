import type { FeesMode, LastDeployedToken } from "$lib/types";

export function passesFundingFeesFilter(
    tokens: readonly LastDeployedToken[] | null | undefined,
    mode: FeesMode = "avg",
    minFeeThreshold = 0,
): boolean {
    const fees = (tokens ?? [])
        .map((token) => token.total_pair_fees_paid)
        .filter((value) => Number.isFinite(value) && value >= 0);

    if (fees.length === 0) return false;
    if (mode === "fixed")
        return fees.every((value) => value >= minFeeThreshold);
    const total = fees.reduce((sum, value) => sum + value, 0);
    return mode === "total"
        ? total >= minFeeThreshold
        : total / fees.length >= minFeeThreshold;
}
