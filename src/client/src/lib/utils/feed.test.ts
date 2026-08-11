import { describe, expect, it } from "vitest";
import { createTokenFeed } from "$lib/components/tokenFeed.fixture";
import type { TokenFeed } from "$lib/types";
import { prependRollingFeed, TOKEN_FEED_LIMIT } from "$lib/utils/feed";

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
