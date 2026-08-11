import type { TokenFeed } from "$lib/types";

export function formatCompactNumber(value: number | null): string {
    if (value === null) return "N/A";
    if (value >= 1e9) return `${(value / 1e9).toFixed(1)}B`;
    if (value >= 1e6) return `${(value / 1e6).toFixed(1)}M`;
    if (value >= 1e3) return `${(value / 1e3).toFixed(1)}K`;
    return value.toFixed(1);
}

export function timeAgo(dateString: string, now = Date.now()): string {
    if (!dateString) return "";

    const timestamp = new Date(dateString).getTime();
    if (!Number.isFinite(timestamp)) return "";

    const seconds = Math.max(0, Math.floor((now - timestamp) / 1000));
    const units = [
        [31_536_000, "y"],
        [2_592_000, "mo"],
        [86_400, "d"],
        [3_600, "h"],
        [60, "m"],
    ] as const;

    for (const [duration, suffix] of units) {
        if (seconds / duration > 1) {
            return `${Math.floor(seconds / duration)}${suffix}`;
        }
    }

    return `${seconds}s`;
}

export function hasRelevantIndicator(feed: TokenFeed): boolean {
    return (
        hasIndicator(feed, "dev migrations") ||
        hasIndicator(feed, "last tokens")
    );
}

export function hasIndicator(feed: TokenFeed, name: string): boolean {
    const normalizedName = name.trim().toLowerCase();
    return feed.indicators.some(
        (indicator) => indicator.trim().toLowerCase() === normalizedName,
    );
}
