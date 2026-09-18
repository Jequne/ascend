import { describe, expect, it } from "vitest";
import { parseDesktopBridgeMessage } from "./protocol";

const commandId = "123e4567-e89b-42d3-a456-426614174000";

describe("desktop bridge protocol", () => {
    it.each([
        {
            type: "state",
            protocolVersion: 1,
            mode: "current_axiom_tab",
            bridgeStatus: "ready",
        },
        {
            type: "navigate",
            protocolVersion: 1,
            commandId,
            url: "https://axiom.trade/meme/pair?chain=sol",
            issuedAt: "2026-09-17T12:00:00.000Z",
        },
        {
            type: "mode_result",
            protocolVersion: 1,
            requestId: commandId,
            accepted: true,
            mode: "off",
        },
        {
            type: "pong",
            protocolVersion: 1,
            sentAt: "2026-09-17T12:00:00.000Z",
        },
    ])("parses $type", (message) => {
        expect(parseDesktopBridgeMessage(JSON.stringify(message))).toEqual(
            message,
        );
    });

    it.each([
        "not json",
        JSON.stringify({
            type: "state",
            protocolVersion: 2,
            mode: "off",
            bridgeStatus: "ready",
        }),
        JSON.stringify({
            type: "state",
            protocolVersion: 1,
            mode: "other",
            bridgeStatus: "ready",
        }),
        JSON.stringify({
            type: "navigate",
            protocolVersion: 1,
            commandId,
            url: "https://axiom.trade.evil.test/meme/pair?chain=sol",
            issuedAt: "2026-09-17T12:00:00.000Z",
        }),
        JSON.stringify({
            type: "pong",
            protocolVersion: 1,
            sentAt: "2026-09-17T12:00:00.000Z",
            pairingSecret: "must-not-be-accepted",
        }),
    ])("rejects malformed or unsafe payload %#", (message) => {
        expect(parseDesktopBridgeMessage(message)).toBeNull();
    });
});
