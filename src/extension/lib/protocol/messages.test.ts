import { describe, expect, it } from "vitest";
import {
    isInternalResponse,
    parseContentNavigateRequest,
    parseInternalRequest,
    parseNavigationResult,
} from "./messages";

const commandId = "123e4567-e89b-42d3-a456-426614174000";

describe("internal protocol parsing", () => {
    it("parses known popup and navigation requests", () => {
        expect(parseInternalRequest({ type: "get_popup_state" })).toEqual({
            type: "get_popup_state",
        });
        expect(
            parseInternalRequest({
                type: "navigate_target",
                commandId,
                url: "https://axiom.trade/meme/pair?chain=sol",
                issuedAt: "2026-09-17T12:00:00.000Z",
            }),
        ).toMatchObject({ type: "navigate_target", commandId });
    });

    it.each([
        null,
        [],
        { type: "unknown" },
        { type: "navigate_target", commandId: "not-a-uuid" },
        {
            type: "navigate_target",
            commandId,
            url: "https://axiom.trade/meme/pair?chain=sol",
            issuedAt: "yesterday",
        },
    ])("rejects malformed request %#", (message) => {
        expect(parseInternalRequest(message)).toBeNull();
    });

    it("parses content commands and navigation results", () => {
        expect(
            parseContentNavigateRequest({
                type: "content_navigate",
                commandId,
                url: "https://axiom.trade/meme/pair?chain=sol",
            }),
        ).toMatchObject({ commandId });
        expect(
            parseNavigationResult({
                commandId,
                status: "completed",
                method: "history",
            }),
        ).toEqual({ commandId, status: "completed", method: "history" });
        expect(
            parseNavigationResult({
                commandId,
                status: "completed",
                method: "new_tab",
            }),
        ).toBeNull();
    });

    it("validates response payloads instead of trusting their discriminator", () => {
        expect(
            isInternalResponse({
                type: "popup_state",
                state: {
                    activePage: { kind: "other" },
                    target: { kind: "idle" },
                },
            }),
        ).toBe(true);
        expect(isInternalResponse({ type: "popup_state" })).toBe(false);
        expect(
            isInternalResponse({
                type: "action_result",
                ok: false,
                state: {
                    activePage: { kind: "other" },
                    target: { kind: "idle" },
                },
            }),
        ).toBe(false);
    });
});
