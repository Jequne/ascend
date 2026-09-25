import { describe, expect, it } from "vitest";
import {
    createLastDeployedToken,
    createTokenFeed,
} from "$lib/components/tokenFeed.fixture";
import { DEFAULT_FILTERS } from "$lib/config/constants";
import { normalizeFilters } from "$lib/config/settings";
import type { FilterSnapshot, TokenFeed, TokenFeedPayload } from "$lib/types";
import { createBlacklistMatcher } from "$lib/utils/blacklist";
import {
    evaluateTokenFeed,
    prependRollingFeed,
    TOKEN_FEED_LIMIT,
} from "$lib/utils/feed";

function createPayload(
    overrides: Partial<TokenFeedPayload> = {},
): TokenFeedPayload {
    const { clientKey, indicators, ...payload } = createTokenFeed();
    void clientKey;
    void indicators;
    return { ...payload, ...overrides };
}

function createSnapshot(
    overrides: Partial<FilterSnapshot["filters"]> = {},
): FilterSnapshot {
    const filters = normalizeFilters({ ...DEFAULT_FILTERS, ...overrides });
    return {
        filters,
        blacklistMatcher: createBlacklistMatcher(filters.blacklist),
    };
}

describe("prependRollingFeed", () => {
    it("keeps only the latest 30 cards and removes the oldest one", () => {
        let feeds: TokenFeed[] = [];

        for (let index = 0; index <= TOKEN_FEED_LIMIT; index += 1) {
            feeds = prependRollingFeed(
                feeds,
                createTokenFeed({
                    clientKey: `pair:${index}`,
                    pair_address: `pair-${index}`,
                }),
            );
        }

        expect(feeds).toHaveLength(TOKEN_FEED_LIMIT);
        expect(feeds[0]?.clientKey).toBe("pair:30");
        expect(feeds.at(-1)?.clientKey).toBe("pair:1");
    });
});

describe("evaluateTokenFeed", () => {
    it("normalizes an accepted payload using one prepared snapshot", () => {
        const decision = evaluateTokenFeed(
            createPayload(),
            createSnapshot(),
            "pair:7",
        );

        expect(decision).toMatchObject({
            accepted: true,
            reason: null,
            feed: {
                clientKey: "pair:7",
                indicators: ["Dev Migrations"],
                last_deployed_tokens: [],
            },
        });
    });

    it.each([
        {
            reason: "blacklist",
            payload: createPayload({ dev_wallet: "blocked-wallet" }),
            snapshot: createSnapshot({ blacklist: ["blocked"] }),
        },
        {
            reason: "dev-holds",
            payload: createPayload({ dev_holds_percent: null }),
            snapshot: createSnapshot(),
        },
        {
            reason: "fees",
            payload: createPayload({
                last_deployed_tokens: [
                    createLastDeployedToken({ total_pair_fees_paid: 1 }),
                ],
            }),
            snapshot: createSnapshot({ minLastTokenFees: 2 }),
        },
        {
            reason: "migration",
            payload: createPayload({
                migrated_tokens_count: 0,
                all_tokens_count: 10,
            }),
            snapshot: createSnapshot({ minMigrationPercent: 10 }),
        },
    ])(
        "returns the $reason rejection reason",
        ({ reason, payload, snapshot }) => {
            expect(evaluateTokenFeed(payload, snapshot, "pair:0")).toEqual({
                accepted: false,
                feed: null,
                reason,
            });
        },
    );

    it("rejects a new token when its ticker contains a blacklist fragment", () => {
        const decision = evaluateTokenFeed(
            createPayload({
                token_name: "no buy",
                token_ticker: "antisniper",
            }),
            createSnapshot({ blacklist: ["snipe"] }),
            "screenshot-pair:0",
        );

        expect(decision).toEqual({
            accepted: false,
            feed: null,
            reason: "blacklist",
        });
    });

    it("allows the last-token override and marks the resulting feed", () => {
        const decision = evaluateTokenFeed(
            createPayload({
                migrated_tokens_count: 0,
                last_deployed_tokens: [createLastDeployedToken()],
            }),
            createSnapshot({
                lastTokensRequiredCount: 1,
                minLastTokenAthMcap: 100_000,
            }),
            "pair:8",
        );

        expect(decision.accepted).toBe(true);
        if (decision.accepted) {
            expect(decision.feed.indicators).toContain("last tokens");
        }
    });

    it("accepts funding history independently of migration and developer fees", () => {
        const decision = evaluateTokenFeed(
            createPayload({
                migrated_tokens_count: 0,
                funding_wallet: "funding-wallet",
                funding_migrated_tokens_count: 1,
                funding_all_tokens_count: 2,
                funding_deployed_tokens: [createLastDeployedToken()],
                last_deployed_tokens: [
                    createLastDeployedToken({ total_pair_fees_paid: 0 }),
                ],
            }),
            createSnapshot({ minLastTokenFees: 5 }),
            "funding-pair:0",
        );
        expect(decision.accepted).toBe(true);
        if (decision.accepted) {
            expect(decision.feed.indicators).toEqual(["Dev Funding"]);
            expect(decision.feed.funding_deployed_tokens).toHaveLength(1);
        }
    });

    it("does not accept funding without a verified previous token", () => {
        const decision = evaluateTokenFeed(
            createPayload({
                migrated_tokens_count: 0,
                funding_wallet: "funding-wallet",
                funding_migrated_tokens_count: 1,
                funding_all_tokens_count: 2,
                funding_deployed_tokens: [],
            }),
            createSnapshot(),
            "funding-pair:0",
        );
        expect(decision.accepted).toBe(false);
    });

    it("uses separate funding fees and ignores the funding history when disabled", () => {
        const payload = createPayload({
            migrated_tokens_count: 0,
            funding_wallet: "funding-wallet",
            funding_migrated_tokens_count: 1,
            funding_all_tokens_count: 2,
            funding_deployed_tokens: [
                createLastDeployedToken({ total_pair_fees_paid: 1 }),
                createLastDeployedToken({ total_pair_fees_paid: 3 }),
            ],
        });
        const options = {
            minLastTokenFees: 100,
            fundingFeesMode: "total" as const,
            minFundingTokenFees: 4,
        };
        const accepted = evaluateTokenFeed(
            payload,
            createSnapshot(options),
            "pair:1",
        );
        expect(accepted.accepted).toBe(true);
        if (accepted.accepted)
            expect(accepted.feed.indicators).toEqual(["Dev Funding"]);

        expect(
            evaluateTokenFeed(
                payload,
                createSnapshot({ ...options, minFundingTokenFees: 5 }),
                "pair:1",
            ).accepted,
        ).toBe(false);
        expect(
            evaluateTokenFeed(
                payload,
                createSnapshot({ ...options, fundingEnabled: false }),
                "pair:1",
            ).accepted,
        ).toBe(false);
    });

    it("rejects funding when the wallet migration rate is below its own minimum", () => {
        const decision = evaluateTokenFeed(
            createPayload({
                migrated_tokens_count: 0,
                funding_wallet: "funding-wallet",
                funding_deployed_tokens: [createLastDeployedToken()],
                funding_migrated_tokens_count: 1,
                funding_all_tokens_count: 20,
            }),
            createSnapshot({ minFundingMigrationPercent: 10 }),
            "funding-low-rate",
        );
        expect(decision.accepted).toBe(false);
    });

    it("accepts Last Tokens when developer fees do not pass", () => {
        const decision = evaluateTokenFeed(
            createPayload({
                migrated_tokens_count: 0,
                last_deployed_tokens: [
                    createLastDeployedToken({
                        total_pair_fees_paid: null,
                        ath_mcap_in_usd: 200_000,
                    }),
                ],
            }),
            createSnapshot({
                minLastTokenFees: 50,
                minLastTokenAthMcap: 100_000,
                lastTokensRequiredCount: 1,
            }),
            "pair:1",
        );
        expect(decision.accepted).toBe(true);
        if (decision.accepted)
            expect(decision.feed.indicators).toEqual(["last tokens"]);
    });

    it("does not treat unknown developer fees as a zero fee for migrations", () => {
        const decision = evaluateTokenFeed(
            createPayload({
                migrated_tokens_count: 1,
                all_tokens_count: 1,
                last_deployed_tokens: [
                    createLastDeployedToken({ total_pair_fees_paid: null }),
                ],
            }),
            createSnapshot(),
            "pair:unknown-fees",
        );
        expect(decision.accepted).toBe(false);
        expect(
            evaluateTokenFeed(
                createPayload({
                    last_deployed_tokens: null,
                    migrated_tokens_count: 0,
                    all_tokens_count: 0,
                }),
                createSnapshot({ minMigrationPercent: 0 }),
                "pair:unknown-history",
            ).accepted,
        ).toBe(false);
    });

    it("accepts a zero-hold developer at the inclusive default boundary", () => {
        const decision = evaluateTokenFeed(
            createPayload({
                dev_holds_percent: 0,
                migrated_tokens_count: 29,
                all_tokens_count: 113,
                last_deployed_tokens: [
                    createLastDeployedToken({
                        token_ticker: "HARAMBE",
                        total_pair_fees_paid: 11.843404087025,
                    }),
                    createLastDeployedToken({
                        token_ticker: "4D",
                        total_pair_fees_paid: 13.9822560376,
                    }),
                    createLastDeployedToken({
                        token_ticker: "KHAT",
                        total_pair_fees_paid: 8.292103633575,
                    }),
                ],
            }),
            createSnapshot({
                minMigrationPercent: 25,
                minLastTokenFees: 10,
                feesMode: "avg",
            }),
            "screenshot-pair:0",
        );

        expect(decision).toMatchObject({
            accepted: true,
            reason: null,
            feed: {
                clientKey: "screenshot-pair:0",
                dev_holds_percent: 0,
            },
        });
    });
});
