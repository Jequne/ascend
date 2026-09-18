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
                bridge: {
                    connection: "connected",
                    mode: "off",
                    reconnectAttempt: 0,
                },
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
                    bridge: {
                        connection: "connected",
                        mode: "off",
                        reconnectAttempt: 0,
                    },
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
                    bridge: {
                        connection: "connected",
                        mode: "current_axiom_tab",
                        reconnectAttempt: 0,
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
        expect(screen.getByText("Running in: Axiom")).toBeVisible();
        expect(
            screen.getByText("Current-tab auto-opening is active."),
        ).toBeVisible();
    });

    it("announces a paused target without relying on color", async () => {
        sendPopupRequest.mockResolvedValueOnce({
            type: "popup_state",
            state: {
                activePage: { kind: "other" },
                target: { kind: "paused", reason: "target_closed" },
                bridge: {
                    connection: "connected",
                    mode: "current_axiom_tab",
                    reconnectAttempt: 0,
                },
            },
        });
        render(App);

        expect(
            await screen.findByText("Paused: the selected tab was closed"),
        ).toBeVisible();
    });

    it("does not report a selected target as running while reconnecting", async () => {
        sendPopupRequest.mockResolvedValueOnce({
            type: "popup_state",
            state: {
                activePage: { kind: "other" },
                target: {
                    kind: "running",
                    tabId: 7,
                    title: "Axiom",
                    url: "https://axiom.trade/",
                },
                bridge: {
                    connection: "reconnecting",
                    mode: "current_axiom_tab",
                    reconnectAttempt: 3,
                },
            },
        });
        render(App);

        expect(
            await screen.findByText(
                "Paused: Axiom is selected while desktop reconnects",
            ),
        ).toBeVisible();
        expect(
            screen.getByText(
                "Current-tab mode is paused until the connection and target are ready.",
            ),
        ).toBeVisible();
        expect(screen.queryByText(/auto-opening is active/i)).toBeNull();
    });

    it("explains an incompatible client version", async () => {
        sendPopupRequest.mockResolvedValueOnce({
            type: "popup_state",
            state: {
                activePage: {
                    kind: "axiom",
                    tabId: 7,
                    title: "Axiom",
                    url: "https://axiom.trade/",
                },
                target: { kind: "idle" },
                bridge: {
                    connection: "version_mismatch",
                    mode: "off",
                    reconnectAttempt: 0,
                },
            },
        });
        render(App);

        expect(await screen.findByText("Update required")).toBeVisible();
        expect(
            screen.getByText(
                "Update Ascend or Ascend ext so their versions match.",
            ),
        ).toBeVisible();
    });
});
