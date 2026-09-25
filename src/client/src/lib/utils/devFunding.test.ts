import { describe, expect, it } from "vitest";
import { createLastDeployedToken } from "$lib/components/tokenFeed.fixture";
import { DEFAULT_FILTERS } from "$lib/config/constants";
import { passesDevFundingStrategy } from "$lib/utils/devFunding";

const previousToken = createLastDeployedToken({
    total_pair_fees_paid: 2,
});
const candidate = {
    blockchain: "sol" as const,
    funding_wallet: "funding-wallet",
    funding_deployed_tokens: [previousToken],
    funding_migrated_tokens_count: 1,
    funding_all_tokens_count: 2,
};

describe("Dev Funding strategy", () => {
    it("requires Solana, an immediate funding wallet, and a verified previous token", () => {
        expect(passesDevFundingStrategy(candidate, DEFAULT_FILTERS)).toBe(true);
        expect(
            passesDevFundingStrategy(
                { ...candidate, blockchain: "bsc" },
                DEFAULT_FILTERS,
            ),
        ).toBe(false);
        expect(
            passesDevFundingStrategy(
                { ...candidate, funding_wallet: " " },
                DEFAULT_FILTERS,
            ),
        ).toBe(false);
        expect(
            passesDevFundingStrategy(
                { ...candidate, funding_deployed_tokens: [] },
                DEFAULT_FILTERS,
            ),
        ).toBe(false);
        expect(
            passesDevFundingStrategy(
                { ...candidate, funding_all_tokens_count: null },
                DEFAULT_FILTERS,
            ),
        ).toBe(false);
        expect(
            passesDevFundingStrategy(
                {
                    ...candidate,
                    funding_deployed_tokens: [
                        createLastDeployedToken({ total_pair_fees_paid: null }),
                    ],
                },
                DEFAULT_FILTERS,
            ),
        ).toBe(false);
    });

    it("uses its own migration and fees thresholds", () => {
        const unrelatedSettings = {
            ...DEFAULT_FILTERS,
            fundingFeesMode: "fixed" as const,
            minFundingTokenFees: 2,
            minLastTokenFees: 100,
            minMigrationPercent: 100,
        };
        expect(passesDevFundingStrategy(candidate, unrelatedSettings)).toBe(
            true,
        );
        expect(
            passesDevFundingStrategy(candidate, {
                ...DEFAULT_FILTERS,
                minFundingMigrationPercent: 51,
            }),
        ).toBe(false);
        expect(
            passesDevFundingStrategy(
                { ...candidate, funding_migrated_tokens_count: 0 },
                DEFAULT_FILTERS,
            ),
        ).toBe(false);
        expect(
            passesDevFundingStrategy(candidate, {
                ...DEFAULT_FILTERS,
                minFundingMigrationPercent: 50,
            }),
        ).toBe(true);
        expect(
            passesDevFundingStrategy(candidate, {
                ...DEFAULT_FILTERS,
                fundingFeesMode: "fixed",
                minFundingTokenFees: 2.1,
            }),
        ).toBe(false);
        expect(
            passesDevFundingStrategy(candidate, {
                ...DEFAULT_FILTERS,
                fundingEnabled: false,
            }),
        ).toBe(false);
    });
});
