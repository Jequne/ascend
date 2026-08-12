import { createTokenFeed } from "$lib/components/tokenFeed.fixture";
import { describe, expect, it } from "vitest";
import { resolveTokenImageUrl } from "./tokenImage";

describe("token image URL", () => {
    it("keeps the image supplied by the realtime feed", () => {
        expect(
            resolveTokenImageUrl(
                createTokenFeed({
                    token_image: " https://cdn.example/token.webp ",
                }),
            ),
        ).toBe("https://cdn.example/token.webp");
    });

    it("derives the Axiom CDN image for a fresh Solana token", () => {
        const tokenAddress = "9LoWfvBgTzwqAMzNeMRwVY8YFBY8hEZjyvo3Mvb8pump";

        expect(
            resolveTokenImageUrl(
                createTokenFeed({
                    blockchain: "sol",
                    token_address: tokenAddress,
                    token_image: null,
                }),
            ),
        ).toBe(
            `https://axiomtrading.sfo3.cdn.digitaloceanspaces.com/${tokenAddress}.webp`,
        );
    });

    it("does not invent URLs for unsupported or invalid addresses", () => {
        expect(
            resolveTokenImageUrl(
                createTokenFeed({
                    blockchain: "bsc",
                    token_address: "0x1234",
                    token_image: null,
                }),
            ),
        ).toBeNull();
        expect(
            resolveTokenImageUrl(
                createTokenFeed({
                    blockchain: "sol",
                    token_address: "invalid-address",
                    token_image: null,
                }),
            ),
        ).toBeNull();
    });
});
