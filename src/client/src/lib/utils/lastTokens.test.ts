import { describe, expect, it } from "vitest";
import { createLastDeployedToken } from "$lib/components/tokenFeed.fixture";
import { passesLastTokensFilter } from "$lib/utils/lastTokens";

describe("last token override", () => {
    const qualifyingToken = createLastDeployedToken({
        ath_mcap_in_usd: 100_000,
    });
    const lowToken = createLastDeployedToken({ ath_mcap_in_usd: 99_999 });

    it("is disabled when the required count is zero", () => {
        expect(
            passesLastTokensFilter([qualifyingToken], {
                minAthMcapThreshold: 100_000,
                requiredCount: 0,
            }),
        ).toBe(false);
    });

    it("accepts ATH values on the boundary and enforces the required count", () => {
        expect(
            passesLastTokensFilter([qualifyingToken, lowToken], {
                minAthMcapThreshold: 100_000,
                requiredCount: 1,
            }),
        ).toBe(true);
        expect(
            passesLastTokensFilter([qualifyingToken, lowToken], {
                minAthMcapThreshold: 100_000,
                requiredCount: 2,
            }),
        ).toBe(false);
    });

    it("considers no more than the latest three tokens", () => {
        expect(
            passesLastTokensFilter(
                [lowToken, lowToken, lowToken, qualifyingToken],
                {
                    minAthMcapThreshold: 100_000,
                    requiredCount: 1,
                },
            ),
        ).toBe(false);
    });
});
