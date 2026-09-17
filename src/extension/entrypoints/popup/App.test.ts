import { cleanup, render, screen, waitFor } from "@testing-library/svelte";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App.svelte";

const { sendPopupRequest } = vi.hoisted(() => ({
    sendPopupRequest: vi.fn(),
}));

vi.mock("../../lib/popup/client", () => ({
    sendPopupRequest,
}));

afterEach(() => {
    cleanup();
    sendPopupRequest.mockReset();
});

describe("popup target controls", () => {
    it("disables start outside Axiom and explains the required action", async () => {
        sendPopupRequest.mockResolvedValueOnce({
            type: "popup_state",
            state: {
                activePage: { kind: "other" },
                target: { kind: "idle" },
            },
        });

        render(App);

        const button = await screen.findByRole("button", {
            name: "Start auto-opening here",
        });
        expect(button).toBeDisabled();
        expect(screen.getByText("https://axiom.trade")).toBeVisible();
        expect(screen.getByText("No Axiom tab selected")).toBeVisible();
    });

    it("starts on an eligible tab and exposes a stop action", async () => {
        sendPopupRequest
            .mockResolvedValueOnce({
                type: "popup_state",
                state: {
                    activePage: {
                        kind: "axiom",
                        tabId: 7,
                        title: "Axiom",
                        url: "https://axiom.trade/",
                    },
                    target: { kind: "idle" },
                },
            })
            .mockResolvedValueOnce({
                type: "action_result",
                ok: true,
                state: {
                    activePage: {
                        kind: "axiom",
                        tabId: 7,
                        title: "Axiom",
                        url: "https://axiom.trade/",
                    },
                    target: {
                        kind: "running",
                        tabId: 7,
                        title: "Axiom",
                        url: "https://axiom.trade/",
                    },
                },
            });
        const user = userEvent.setup();
        render(App);

        const start = await screen.findByRole("button", {
            name: "Start auto-opening here",
        });
        expect(start).toBeEnabled();
        await user.click(start);

        await waitFor(() =>
            expect(
                screen.getByRole("button", { name: "Stop auto-opening" }),
            ).toBeEnabled(),
        );
        expect(screen.getByText("Selected: Axiom")).toBeVisible();
    });

    it("announces a paused target without relying on color", async () => {
        sendPopupRequest.mockResolvedValueOnce({
            type: "popup_state",
            state: {
                activePage: { kind: "other" },
                target: { kind: "paused", reason: "target_closed" },
            },
        });
        render(App);

        expect(
            await screen.findByText("Paused: the selected tab was closed"),
        ).toBeVisible();
    });
});
