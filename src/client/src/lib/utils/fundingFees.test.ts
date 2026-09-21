import { describe, expect, it } from "vitest";
import { createLastDeployedToken } from "$lib/components/tokenFeed.fixture";
import { passesFundingFeesFilter } from "$lib/utils/fundingFees";

describe("passesFundingFeesFilter", () => {
    it("requires a previous token with valid fees", () => {
        expect(passesFundingFeesFilter([])).toBe(false);
        expect(
            passesFundingFeesFilter([
                createLastDeployedToken({ total_pair_fees_paid: Number.NaN }),
            ]),
        ).toBe(false);
        expect(passesFundingFeesFilter([createLastDeployedToken()])).toBe(true);
    });

    it("evaluates avg, total, and fixed independently", () => {
        const tokens = [
            createLastDeployedToken({ total_pair_fees_paid: 1 }),
            createLastDeployedToken({ total_pair_fees_paid: 3 }),
        ];
        expect(passesFundingFeesFilter(tokens, "avg", 2)).toBe(true);
        expect(passesFundingFeesFilter(tokens, "total", 4)).toBe(true);
        expect(passesFundingFeesFilter(tokens, "fixed", 2)).toBe(false);
    });
});
