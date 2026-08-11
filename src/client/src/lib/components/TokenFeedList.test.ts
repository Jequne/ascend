import { render, screen } from "@testing-library/svelte";
import { tick } from "svelte";
import { afterEach, describe, expect, it } from "vitest";
import { wsStore } from "$lib/stores/websocket.svelte";
import TokenFeedList from "./TokenFeedList.svelte";
import { createTokenFeed } from "./tokenFeed.fixture";

describe("TokenFeedList", () => {
    afterEach(() => {
        wsStore.clearTokens();
    });

    it("preserves existing keyed cards when a new feed is prepended", async () => {
        const first = createTokenFeed({ clientKey: "pair-a:0" });
        wsStore.tokenFeeds = [first];
        render(TokenFeedList);
        const existingCard = screen.getByTestId("token-card");

        wsStore.tokenFeeds = [
            createTokenFeed({
                clientKey: "pair-b:1",
                pair_address: "pair-b",
                token_name: "Second Token",
            }),
            first,
        ];
        await tick();

        expect(screen.getAllByTestId("token-card")[1]).toBe(existingCard);
    });
});
