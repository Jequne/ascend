import { createTokenFeed } from "$lib/components/tokenFeed.fixture";
import { describe, expect, it } from "vitest";
import { resolveTokenImageUrls } from "./tokenImage";

describe("token image URL", () => {
    it("keeps the image supplied by the realtime feed", () => {
        expect(
            resolveTokenImageUrls(
                createTokenFeed({
                    token_image: " https://cdn.example/token.webp ",
                    token_address: "invalid-address",
                }),
            ),
        ).toEqual(["https://cdn.example/token.webp"]);
    });

    it("adds the Axiom CDN image as a fallback for a Solana token", () => {
        const tokenAddress = "9LoWfvBgTzwqAMzNeMRwVY8YFBY8hEZjyvo3Mvb8pump";

        expect(
            resolveTokenImageUrls(
                createTokenFeed({
                    blockchain: "sol",
                    token_address: tokenAddress,
                    token_image: "https://origin.example/token.webp",
                }),
            ),
        ).toEqual([
            "https://origin.example/token.webp",
            `https://axiomtrading.sfo3.cdn.digitaloceanspaces.com/${tokenAddress}.webp`,
        ]);
    });

    it("does not invent URLs for unsupported or invalid addresses", () => {
        expect(
            resolveTokenImageUrls(
                createTokenFeed({
                    blockchain: "bsc",
                    token_address: "0x1234",
                    token_image: null,
                }),
            ),
        ).toEqual([]);
        expect(
            resolveTokenImageUrls(
                createTokenFeed({
                    blockchain: "sol",
                    token_address: "invalid-address",
                    token_image: null,
                }),
            ),
        ).toEqual([]);
    });

    it("deduplicates a supplied Axiom CDN image", () => {
        const tokenAddress = "9LoWfvBgTzwqAMzNeMRwVY8YFBY8hEZjyvo3Mvb8pump";
        const imageUrl = `https://axiomtrading.sfo3.cdn.digitaloceanspaces.com/${tokenAddress}.webp`;

        expect(
            resolveTokenImageUrls(
                createTokenFeed({
                    token_address: tokenAddress,
                    token_image: imageUrl,
                }),
            ),
        ).toEqual([imageUrl]);
    });
});
