import { describe, expect, it, vi } from "vitest";
import { createTokenFeed } from "$lib/components/tokenFeed.fixture";
import { DEFAULT_FILTERS } from "$lib/config/constants";
import { normalizeFilters } from "$lib/config/settings";
import { DefaultAutoOpenDispatcher } from "$lib/services/autoOpen";
import type { ExtensionBridgeService } from "$lib/services/extensionBridge";
import type { UrlOpener } from "$lib/services/opener";
import type { AutoOpenMode, FilterSnapshot, Terminal } from "$lib/types";

function createSnapshot(
    autoOpenMode: AutoOpenMode,
    terminal: Terminal = "axiom",
): FilterSnapshot {
    return {
        filters: normalizeFilters({
            ...DEFAULT_FILTERS,
            autoOpenMode,
            terminal,
        }),
        blacklistMatcher: null,
    };
}

function createHarness() {
    const open = vi.fn<UrlOpener["open"]>().mockResolvedValue();
    const navigate = vi
        .fn<ExtensionBridgeService["navigate"]>()
        .mockResolvedValue();
    const bridge: ExtensionBridgeService = {
        getState: vi.fn(),
        getPairingCode: vi.fn(),
        rotatePairingCode: vi.fn(),
        setMode: vi.fn(),
        navigate,
    };
    return {
        open,
        navigate,
        dispatcher: new DefaultAutoOpenDispatcher({ open }, bridge),
    };
}

describe("DefaultAutoOpenDispatcher", () => {
    it("performs no side effect while off", () => {
        const { dispatcher, open, navigate } = createHarness();
        dispatcher.dispatch(createTokenFeed(), createSnapshot("off"));
        expect(open).not.toHaveBeenCalled();
        expect(navigate).not.toHaveBeenCalled();
    });

    it.each([
        ["axiom", "https://axiom.trade/meme/pair?chain=sol"],
        ["gmgn", "https://gmgn.ai/sol/token/token"],
    ] as const)("uses only the existing %s new-tab opener", (terminal, url) => {
        const { dispatcher, open, navigate } = createHarness();
        dispatcher.dispatch(
            createTokenFeed(),
            createSnapshot("new_tab", terminal),
        );
        expect(open).toHaveBeenCalledOnce();
        expect(open).toHaveBeenCalledWith(url);
        expect(navigate).not.toHaveBeenCalled();
    });

    it("routes current-tab mode only through the bridge with a validated Axiom URL", () => {
        const { dispatcher, open, navigate } = createHarness();
        dispatcher.dispatch(
            createTokenFeed(),
            createSnapshot("current_axiom_tab", "gmgn"),
        );
        expect(open).not.toHaveBeenCalled();
        expect(navigate).toHaveBeenCalledOnce();
        expect(navigate).toHaveBeenCalledWith(
            expect.objectContaining({
                commandId: expect.any(String),
                url: "https://axiom.trade/meme/pair?chain=sol",
                issuedAt: expect.any(String),
            }),
        );
    });

    it("never falls back to new_tab when the bridge rejects", async () => {
        const { dispatcher, open, navigate } = createHarness();
        const consoleError = vi
            .spyOn(console, "error")
            .mockImplementation(() => undefined);
        navigate.mockRejectedValue(new Error("extension unavailable"));
        dispatcher.dispatch(
            createTokenFeed(),
            createSnapshot("current_axiom_tab"),
        );
        await Promise.resolve();
        expect(open).not.toHaveBeenCalled();
        expect(consoleError).toHaveBeenCalledOnce();
    });
});
