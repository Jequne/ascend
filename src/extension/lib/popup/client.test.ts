import { beforeEach, describe, expect, it } from "vitest";
import { fakeBrowser } from "wxt/testing/fake-browser";
import { sendPopupRequest } from "./client";

describe("popup browser client", () => {
    beforeEach(() => {
        fakeBrowser.reset();
    });

    it("uses the extension runtime and validates the response", async () => {
        fakeBrowser.runtime.onMessage.addListener(
            (_message, _sender, sendResponse) => {
                sendResponse({
                    type: "popup_state",
                    state: {
                        activePage: { kind: "other" },
                        target: { kind: "idle" },
                    },
                });
                return true;
            },
        );

        await expect(
            sendPopupRequest({ type: "get_popup_state" }),
        ).resolves.toMatchObject({ type: "popup_state" });
    });

    it("rejects a malformed background response", async () => {
        fakeBrowser.runtime.onMessage.addListener(
            (_message, _sender, sendResponse) => {
                sendResponse({ type: "popup_state" });
                return true;
            },
        );

        await expect(
            sendPopupRequest({ type: "get_popup_state" }),
        ).rejects.toThrow("invalid_background_response");
    });
});
