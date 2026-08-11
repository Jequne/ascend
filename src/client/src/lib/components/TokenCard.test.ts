import { openUrl } from "@tauri-apps/plugin-opener";
import { fireEvent, render, screen } from "@testing-library/svelte";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { filtersStore } from "$lib/stores/filters.svelte";
import TokenCard from "./TokenCard.svelte";
import { createLastDeployedToken, createTokenFeed } from "./tokenFeed.fixture";

vi.mock("@tauri-apps/plugin-opener", () => ({
    openUrl: vi.fn(() => Promise.resolve()),
}));

describe("TokenCard", () => {
    beforeEach(() => {
        vi.mocked(openUrl).mockClear();
        filtersStore.blacklist = [];
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
