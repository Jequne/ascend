import { describe, expect, it } from "vitest";
import { createTokenFeed } from "$lib/components/tokenFeed.fixture";
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
});
