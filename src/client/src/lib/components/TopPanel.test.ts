import { render, screen } from "@testing-library/svelte";
import { tick } from "svelte";
import { afterEach, describe, expect, it } from "vitest";
import { wsStore } from "$lib/stores/websocket.svelte";
import TopPanel from "./TopPanel.svelte";
import { createTokenFeed } from "./tokenFeed.fixture";

describe("TopPanel feed controls", () => {
    afterEach(() => {
        wsStore.clearTokens();
    });

    it("provides accessible settings and clear controls with disabled state", async () => {
        render(TopPanel);

        expect(
            screen.getByRole("button", { name: "Open settings" }),
        ).toBeEnabled();
        const clearButton = screen.getByRole("button", {
            name: "Clear visible tokens",
        });
        expect(clearButton).toBeDisabled();

        wsStore.tokenFeeds = [createTokenFeed()];
        await tick();

        expect(clearButton).toBeEnabled();
    });
});
