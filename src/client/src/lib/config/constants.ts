import type { FilterSettings } from "$lib/types";

export const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";
export const WS_BASE_URL =
    import.meta.env.VITE_WS_BASE_URL ?? "ws://localhost:8000/ws";

export const LAST_TOKEN_FEES_AGE_EXCLUSION_DAYS = 310;

export const DEFAULT_FILTERS = {
    minDevHoldsPercent: 0.1,
    maxDevHoldsPercent: 100,
    minMigrationPercent: 10,
    feesMode: "avg",
    minLastTokenFees: 0,
    minLastTokenAthMcap: 0,
    lastTokensRequiredCount: 0,
    blacklist: [],
    terminal: "axiom",
    autoOpenInNewTab: false,
    highlightMigratedTokens: true,
} satisfies FilterSettings;
