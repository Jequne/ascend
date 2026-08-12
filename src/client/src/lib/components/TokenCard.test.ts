import { openUrl } from "@tauri-apps/plugin-opener";
import { fireEvent, render, screen } from "@testing-library/svelte";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { tick } from "svelte";
import { DEFAULT_FILTERS } from "$lib/config/constants";
import { filtersStore } from "$lib/stores/filters.svelte";
import TokenCard from "./TokenCard.svelte";
import { createLastDeployedToken, createTokenFeed } from "./tokenFeed.fixture";

vi.mock("@tauri-apps/plugin-opener", () => ({
    openUrl: vi.fn(() => Promise.resolve()),
}));

describe("TokenCard", () => {
    beforeEach(() => {
        vi.mocked(openUrl).mockClear();
        filtersStore.updateFilters(DEFAULT_FILTERS);
    });

    it("marks migrated previous tokens and toggles their row highlight", async () => {
        render(TokenCard, {
            feed: createTokenFeed({
                last_deployed_tokens: [createLastDeployedToken()],
            }),
        });

        const migratedRow = screen.getByRole("button", {
            name: /Open Last Token/,
        });
        expect(screen.getByLabelText("Migrated token")).toHaveTextContent("M");
        expect(migratedRow).toHaveAttribute("data-migrated", "true");
        expect(migratedRow).toHaveAttribute("data-highlighted", "true");

        filtersStore.highlightMigratedTokens = false;
        await tick();

        expect(
            screen.getByRole("button", { name: /Open Last Token/ }),
        ).toHaveAttribute("data-highlighted", "false");
        expect(screen.getByLabelText("Migrated token")).toBeVisible();
    });

    it("renders the existing data order and nested last tokens", () => {
        render(TokenCard, {
            feed: createTokenFeed({
                last_deployed_tokens: [createLastDeployedToken()],
            }),
        });

        const card = screen.getByTestId("token-card");
        expect(card).toHaveTextContent("$EXM");
        expect(card).toHaveTextContent("Example Token");
        expect(card).toHaveTextContent("DH: 4.2%");
        expect(card).toHaveTextContent("4 migrated");
        expect(card).toHaveTextContent("Last Tokens");
        expect(card).toHaveTextContent("$LAST");
    });

    it("exposes indicator-specific card glow states", () => {
        const { rerender } = render(TokenCard, {
            feed: createTokenFeed(),
        });

        const card = screen.getByTestId("token-card");
        expect(card).toHaveAttribute("data-dev-migrations", "true");
        expect(card).toHaveAttribute("data-last-tokens", "false");

        rerender({
            feed: createTokenFeed({
                indicators: ["Dev Migrations", "Last Tokens"],
            }),
        });

        expect(card).toHaveAttribute("data-dev-migrations", "true");
        expect(card).toHaveAttribute("data-last-tokens", "true");
        expect(screen.getByText("Last Tokens")).toHaveClass("text-[#e2ca67]");
    });

    it("opens accessible social links through the opener service", async () => {
        render(TokenCard, { feed: createTokenFeed() });

        const xLink = screen.getByRole("link", { name: "Open X profile" });
        expect(xLink).toHaveAttribute("title", "X");
        expect(xLink.querySelector("img")).toHaveAttribute(
            "src",
            "/icons/x.svg",
        );

        await fireEvent.click(xLink);

        expect(openUrl).toHaveBeenCalledOnce();
        expect(openUrl).toHaveBeenCalledWith("https://x.com/example");
    });

    it("opens the developer X profile from the nickname", async () => {
        render(TokenCard, {
            feed: createTokenFeed({ twitter_admin_nickname: "@Eustazzeus" }),
        });

        const adminLink = screen.getByRole("link", {
            name: "Open @Eustazzeus on X",
        });
        expect(adminLink).toHaveAttribute("href", "https://x.com/Eustazzeus");

        await fireEvent.click(adminLink);

        expect(openUrl).toHaveBeenCalledWith("https://x.com/Eustazzeus");
    });

    it("hides an invalid developer X nickname", () => {
        render(TokenCard, {
            feed: createTokenFeed({ twitter_admin_nickname: "not a handle" }),
        });

        expect(
            screen.queryByRole("link", { name: /not a handle.*on X/ }),
        ).not.toBeInTheDocument();
    });

    it("uses the Axiom CDN image when a fresh token has no image URL", () => {
        const tokenAddress = "9LoWfvBgTzwqAMzNeMRwVY8YFBY8hEZjyvo3Mvb8pump";

        render(TokenCard, {
            feed: createTokenFeed({
                token_address: tokenAddress,
                token_image: null,
            }),
        });

        expect(screen.getByRole("img", { name: "EXM token" })).toHaveAttribute(
            "src",
            `https://axiomtrading.sfo3.cdn.digitaloceanspaces.com/${tokenAddress}.webp`,
        );
    });

    it("toggles the developer wallet blacklist", async () => {
        render(TokenCard, { feed: createTokenFeed() });

        const button = screen.getByRole("button", {
            name: "Add developer wallet to blacklist",
        });
        await fireEvent.click(button);

        expect(filtersStore.blacklist).toContain("dev-wallet");
        expect(
            screen.getByRole("button", {
                name: "Remove developer wallet from blacklist",
            }),
        ).toHaveAttribute("aria-pressed", "true");
    });
});
