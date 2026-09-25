import { describe, expect, it } from "vitest";
import {
    createLastDeployedToken,
    createTokenFeed,
} from "$lib/components/tokenFeed.fixture";
import type { TokenFeedPayload } from "$lib/types";
import { parseWebSocketMessage } from "$lib/utils/websocketMessage";

function createPayload(): TokenFeedPayload {
    const { clientKey, indicators, ...payload } = createTokenFeed();
    void clientKey;
    void indicators;
    return payload;
}

describe("parseWebSocketMessage", () => {
    it.each([
        {
            type: "ping",
            message: {
                type: "ping",
                payload: { timestamp: "2026-08-11T12:00:00.000Z" },
            },
        },
        {
            type: "sol_price",
            message: { type: "sol_price", payload: 182.4 },
        },
        {
            type: "token_feed",
            message: { type: "token_feed", payload: createPayload() },
        },
    ])("parses a valid $type message", ({ message }) => {
        expect(parseWebSocketMessage(JSON.stringify(message))).toEqual(message);
    });

    it("rejects malformed JSON, unknown variants, and invalid payloads", () => {
        expect(parseWebSocketMessage("{")).toBeNull();
        expect(
            parseWebSocketMessage(
                JSON.stringify({ type: "unknown", payload: {} }),
            ),
        ).toBeNull();
        expect(
            parseWebSocketMessage(
                JSON.stringify({
                    type: "token_feed",
                    payload: { ...createPayload(), token_address: null },
                }),
            ),
        ).toBeNull();
        expect(parseWebSocketMessage(new Blob())).toBeNull();
    });

    it("accepts separate funding history and rejects unverified funding fees", () => {
        const payload = {
            ...createPayload(),
            funding_wallet: "funding-wallet",
            funding_migrated_tokens_count: 1,
            funding_all_tokens_count: 2,
            funding_deployed_tokens: [createLastDeployedToken()],
        };
        expect(
            parseWebSocketMessage(
                JSON.stringify({ type: "token_feed", payload }),
            ),
        ).toMatchObject({ type: "token_feed", payload });
        expect(
            parseWebSocketMessage(
                JSON.stringify({
                    type: "token_feed",
                    payload: {
                        ...payload,
                        funding_deployed_tokens: [
                            {
                                ...createLastDeployedToken(),
                                total_pair_fees_paid: null,
                            },
                        ],
                    },
                }),
            ),
        ).toBeNull();
        expect(
            parseWebSocketMessage(
                JSON.stringify({
                    type: "token_feed",
                    payload: { ...payload, funding_all_tokens_count: -1 },
                }),
            ),
        ).toBeNull();
    });
});
