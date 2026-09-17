import { describe, expect, it, vi } from "vitest";
import { handleMainWorldNavigation } from "./axiom-main-world";
import {
    parseMainWorldResponse,
    serializeMainWorldMessage,
} from "./axiom-main-world-protocol";

const requestId = "123e4567-e89b-42d3-a456-426614174000";

describe("Axiom main-world navigation", () => {
    it("pushes the validated URL and dispatches popstate with preserved state", () => {
        const state = { routerIndex: 4 };
        const pushState = vi.fn();
        const dispatchPopState = vi.fn();
        const sendResponse = vi.fn();

        handleMainWorldNavigation(
            serializeMainWorldMessage({
                requestId,
                url: "https://axiom.trade/meme/pair?chain=sol",
            }),
            {
                getCurrentUrl: () => "https://axiom.trade/pulse",
                getHistoryState: () => state,
                pushState,
                dispatchPopState,
                sendResponse,
            },
        );

        expect(pushState).toHaveBeenCalledWith(
            state,
            "https://axiom.trade/meme/pair?chain=sol",
        );
        expect(dispatchPopState).toHaveBeenCalledWith(state);
        expect(parseMainWorldResponse(sendResponse.mock.calls[0]?.[0])).toEqual(
            { requestId, ok: true },
        );
    });

    it.each([
        "https://axiom.trade.evil.example/meme/pair?chain=sol",
        "https://axiom.trade/meme/pair?chain=eth",
        "https://axiom.trade/meme/pair?chain=sol&redirect=https://evil.example",
    ])("rejects an unsafe target without changing history: %s", (url) => {
        const pushState = vi.fn();
        const dispatchPopState = vi.fn();
        const sendResponse = vi.fn();

        handleMainWorldNavigation(
            serializeMainWorldMessage({ requestId, url }),
            {
                getCurrentUrl: () => "https://axiom.trade/pulse",
                getHistoryState: () => null,
                pushState,
                dispatchPopState,
                sendResponse,
            },
        );

        expect(pushState).not.toHaveBeenCalled();
        expect(dispatchPopState).not.toHaveBeenCalled();
        expect(parseMainWorldResponse(sendResponse.mock.calls[0]?.[0])).toEqual(
            { requestId, ok: false },
        );
    });

    it("ignores malformed cross-world messages", () => {
        const sendResponse = vi.fn();
        handleMainWorldNavigation("not-json", {
            getCurrentUrl: () => "https://axiom.trade/pulse",
            getHistoryState: () => null,
            pushState: vi.fn(),
            dispatchPopState: vi.fn(),
            sendResponse,
        });
        expect(sendResponse).not.toHaveBeenCalled();
    });
});
