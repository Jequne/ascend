import { describe, expect, it } from "vitest";
import { createLastDeployedToken } from "$lib/components/tokenFeed.fixture";
import {
    getLastTokenFeesSummary,
    passesLastTokenFeesFilter,
} from "$lib/utils/lastTokenFees";

const now = Date.parse("2026-08-11T12:00:00.000Z");

describe("last token fees", () => {
    const tokens = [
        createLastDeployedToken({ total_pair_fees_paid: 1 }),
        createLastDeployedToken({ total_pair_fees_paid: 3 }),
    ];

    it("supports average, total, and fixed fee modes at their boundaries", () => {
        expect(
            passesLastTokenFeesFilter(tokens, {
                mode: "avg",
                minFeeThreshold: 2,
                now,
            }),
        ).toBe(true);
        expect(
            passesLastTokenFeesFilter(tokens, {
                mode: "total",
                minFeeThreshold: 4,
                now,
            }),
        ).toBe(true);
        expect(
            passesLastTokenFeesFilter(tokens, {
                mode: "fixed",
                minFeeThreshold: 2,
                now,
            }),
        ).toBe(false);
    });

    it("excludes only old low-fee tokens from the calculation", () => {
        const oldLowFeeToken = createLastDeployedToken({
            total_pair_fees_paid: 1,
            created_at: "2025-01-01T00:00:00.000Z",
        });
        const recentToken = createLastDeployedToken({
            total_pair_fees_paid: 3,
            created_at: "2026-08-10T00:00:00.000Z",
        });
        const summary = getLastTokenFeesSummary([oldLowFeeToken, recentToken], {
            minFeeThreshold: 2,
            now,
            ageExclusionDays: 310,
        });

        expect(summary).toMatchObject({
            consideredCount: 1,
            totalFees: 3,
            averageFees: 3,
            passesFixed: true,
        });
    });

    it("allows an empty considered set in every mode", () => {
        expect(
            passesLastTokenFeesFilter([], {
                mode: "fixed",
                minFeeThreshold: 100,
                now,
            }),
        ).toBe(true);
    });
});
