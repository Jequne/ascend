import { describe, expect, it } from "vitest";
import { isAxiomPageUrl, validateAxiomTokenUrl } from "./axiom-url";

describe("Axiom URL validation", () => {
    it("accepts exact Axiom token URLs for supported chains", () => {
        expect(
            validateAxiomTokenUrl(
                "https://axiom.trade/meme/pair-address?trackerChains=sol,bsc&chain=sol",
            ),
        ).toEqual({
            ok: true,
            url: "https://axiom.trade/meme/pair-address?chain=sol&trackerChains=sol%2Cbsc",
            chain: "sol",
            address: "pair-address",
        });
        expect(
            validateAxiomTokenUrl(
                "https://axiom.trade/meme/0x0123456789abcdef?chain=bsc",
            ),
        ).toMatchObject({ ok: true, chain: "bsc" });
    });

    it("preserves the network parameters observed on real Axiom token routes", () => {
        expect(
            validateAxiomTokenUrl(
                "https://axiom.trade/meme/F8qFEucvUF9govRejz9zHeUwFEbB8MKnrG4bRDnzkgLT?chain=sol&chains=sol&pulseChains=sol&trackerChains=sol&discoverChains=sol",
            ),
        ).toEqual({
            ok: true,
            url: "https://axiom.trade/meme/F8qFEucvUF9govRejz9zHeUwFEbB8MKnrG4bRDnzkgLT?chain=sol&chains=sol&discoverChains=sol&pulseChains=sol&trackerChains=sol",
            chain: "sol",
            address: "F8qFEucvUF9govRejz9zHeUwFEbB8MKnrG4bRDnzkgLT",
        });
    });

    it.each([
        "http://axiom.trade/meme/pair?chain=sol",
        "https://axiom.trade.evil.example/meme/pair?chain=sol",
        "https://evil.example/?next=https://axiom.trade/meme/pair?chain=sol",
        "https://user:password@axiom.trade/meme/pair?chain=sol",
        "https://axiom.trade:444/meme/pair?chain=sol",
        "https://axiom.trade/meme/?chain=sol",
        "https://axiom.trade/meme/pair/extra?chain=sol",
        "https://axiom.trade/meme/pair%2Fextra?chain=sol",
        "https://axiom.trade/meme/pair?chain=eth",
        "https://axiom.trade/meme/pair?chain=sol&chain=bsc",
        "https://axiom.trade/meme/pair?chain=sol&redirect=https%3A%2F%2Fevil.example",
        "https://axiom.trade/meme/pair?chain=sol#fragment",
    ])("rejects unsafe token URL %s", (url) => {
        expect(validateAxiomTokenUrl(url).ok).toBe(false);
    });

    it("recognizes only exact secure Axiom page origins", () => {
        expect(isAxiomPageUrl("https://axiom.trade/")).toBe(true);
        expect(isAxiomPageUrl("https://axiom.trade/meme/pair?chain=sol")).toBe(
            true,
        );
        expect(isAxiomPageUrl("http://axiom.trade/")).toBe(false);
        expect(isAxiomPageUrl("https://axiom.trade.example/")).toBe(false);
        expect(isAxiomPageUrl("https://axiom.trade:8443/")).toBe(false);
    });
});
