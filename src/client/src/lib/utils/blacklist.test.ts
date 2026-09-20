import { describe, expect, it } from "vitest";
import {
    createBlacklistMatcher,
    normalizeBlacklistEntries,
    tokenMatchesBlacklist,
} from "$lib/utils/blacklist";

describe("blacklist normalization and matching", () => {
    it("trims entries, removes empty values, and deduplicates case-insensitively", () => {
        expect(
            normalizeBlacklistEntries(
                " Wallet-1, wallet-1\n\n Token Name \nTicker",
            ),
        ).toEqual(["Wallet-1", "Token Name", "Ticker"]);
    });

    it("deduplicates apostrophe variants that have identical matching behavior", () => {
        expect(normalizeBlacklistEntries(["don't", "dont", "DON’T"])).toEqual([
            "don't",
        ]);
    });

    it.each([
        { field: "dev_wallet", value: "PREFIX-wallet-1-suffix" },
        { field: "token_name", value: "Example TOKEN name" },
        { field: "token_ticker", value: "ticker" },
        { field: "twitter_admin_nickname", value: "AdminName" },
    ])("matches normalized text in $field", ({ field, value }) => {
        const matcher = createBlacklistMatcher([
            "wallet-1",
            "token",
            "TICKER",
            "adminname",
        ]);

        expect(
            tokenMatchesBlacklist({ [field]: `  ${value}  ` }, matcher),
        ).toBe(true);
    });

    it.each([
        { field: "token_ticker", value: "antisniper", entry: "snipe" },
        {
            field: "token_name",
            value: "supermegasnipecvc",
            entry: "snipe",
        },
        { field: "token_name", value: "DON'T BUY", entry: "dont" },
        { field: "token_name", value: "dont buy", entry: "don't" },
        { field: "token_name", value: "Don’t buy", entry: "DON'T" },
    ])(
        "matches the $entry fragment anywhere in $field",
        ({ field, value, entry }) => {
            expect(
                tokenMatchesBlacklist(
                    { [field]: value },
                    createBlacklistMatcher([entry]),
                ),
            ).toBe(true);
        },
    );

    it("normalizes text passed directly to the prepared matcher", () => {
        expect(
            createBlacklistMatcher(["snipe"])?.matchesText("AntiSniper"),
        ).toBe(true);
    });

    it("returns no matcher for an empty normalized list", () => {
        expect(createBlacklistMatcher([" ", ""])).toBeNull();
    });
});
