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
});
