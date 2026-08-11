import { describe, expect, it } from "vitest";
import { createTokenFeed } from "$lib/components/tokenFeed.fixture";
import { buildTerminalUrl, normalizeExternalUrl } from "$lib/utils/tokenLinks";

describe("token links", () => {
    it("builds the existing Axiom and GMGN terminal routes", () => {
        const token = createTokenFeed({
            blockchain: "sol",
            pair_address: "pair-address",
            token_address: "token-address",
        });

        expect(buildTerminalUrl(token, "axiom")).toBe(
            "https://axiom.trade/meme/pair-address?chain=sol",
        );
        expect(buildTerminalUrl(token, "gmgn")).toBe(
            "https://gmgn.ai/sol/token/token-address",
        );
    });

    it("requires the address selected by the terminal", () => {
        expect(
            buildTerminalUrl(createTokenFeed({ pair_address: "" }), "axiom"),
        ).toBeNull();
        expect(
            buildTerminalUrl(createTokenFeed({ token_address: "" }), "gmgn"),
        ).toBeNull();
    });

    it("rejects malformed and unsafe external URLs", () => {
        expect(normalizeExternalUrl("https://example.com/path")).toBe(
            "https://example.com/path",
        );
        expect(normalizeExternalUrl("javascript:alert(1)")).toBeNull();
        expect(normalizeExternalUrl("file:///tmp/token")).toBeNull();
        expect(normalizeExternalUrl("not a url")).toBeNull();
    });
});
