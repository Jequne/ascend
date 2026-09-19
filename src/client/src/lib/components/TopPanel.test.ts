import { render, screen, within } from "@testing-library/svelte";
import userEvent from "@testing-library/user-event";
import { tick } from "svelte";
import { afterEach, describe, expect, it } from "vitest";
import { wsStore } from "$lib/stores/websocket.svelte";
import { notificationsStore } from "$lib/stores/notifications.svelte";
import { DEFAULT_NOTIFICATIONS } from "$lib/config/constants";
import TopPanel from "./TopPanel.svelte";
import { createTokenFeed } from "./tokenFeed.fixture";

describe("TopPanel feed controls", () => {
    afterEach(() => {
        wsStore.clearTokens();
        notificationsStore.replace(DEFAULT_NOTIFICATIONS);
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

    it("toggles persisted sound state immediately before settings", async () => {
        const user = userEvent.setup();
        render(TopPanel);
        const actions = screen.getByTestId("header-actions");
        const buttons = within(actions).getAllByRole("button");
        const sound = screen.getByRole("button", {
            name: "Disable sound notifications",
        });

        expect(buttons[0]).toBe(sound);
        expect(buttons[1]).toHaveAccessibleName("Open settings");
        expect(sound).toHaveAttribute("aria-pressed", "true");

        await user.click(sound);
        expect(notificationsStore.enabled).toBe(false);
        expect(
            screen.getByRole("button", {
                name: "Enable sound notifications",
            }),
        ).toHaveAttribute("aria-pressed", "false");
    });
});
