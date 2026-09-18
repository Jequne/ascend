import { describe, expect, it, vi } from "vitest";
import {
    createLastDeployedToken,
    createTokenFeed,
} from "$lib/components/tokenFeed.fixture";
import type { ExtensionBridgeService } from "$lib/services/extensionBridge";
import type { UrlOpener } from "$lib/services/opener";
import { TokenNavigationService } from "$lib/services/tokenNavigation";

function createHarness() {
    const open = vi.fn<UrlOpener["open"]>().mockResolvedValue();
    const navigate = vi
        .fn<ExtensionBridgeService["navigate"]>()
        .mockResolvedValue();
    const bridge: ExtensionBridgeService = {
        getState: vi.fn(),
        getPairingCode: vi.fn(),
        rotatePairingCode: vi.fn(),
        prepareInstallation: vi.fn(),
        openInstallationFolder: vi.fn(),
        setMode: vi.fn(),
        navigate,
    };

    return {
        open,
        navigate,
        service: new TokenNavigationService({ open }, bridge),
    };
}

describe("TokenNavigationService", () => {
    it.each(["off", "new_tab"] as const)(
        "keeps manual card navigation in the system opener in %s mode",
        (mode) => {
            const { service, open, navigate } = createHarness();

            service.open(createTokenFeed(), "gmgn", mode);

            expect(open).toHaveBeenCalledWith(
                "https://gmgn.ai/sol/token/token",
            );
            expect(navigate).not.toHaveBeenCalled();
        },
    );

    it.each([
        ["current token", createTokenFeed(), "pair"],
        ["previous token", createLastDeployedToken(), "last-pair"],
    ] as const)(
        "opens a %s in the selected Axiom tab in current-tab mode",
        (_label, token, pairAddress) => {
            const { service, open, navigate } = createHarness();

            service.open(token, "axiom", "current_axiom_tab");

            expect(open).not.toHaveBeenCalled();
            expect(navigate).toHaveBeenCalledWith(
                expect.objectContaining({
                    commandId: expect.any(String),
                    url: `https://axiom.trade/meme/${pairAddress}?chain=sol`,
                    issuedAt: expect.any(String),
                }),
            );
        },
    );

    it("does not fall back to a new tab when current-tab navigation fails", async () => {
        const { service, open, navigate } = createHarness();
        const consoleError = vi
            .spyOn(console, "error")
            .mockImplementation(() => undefined);
        navigate.mockRejectedValue(new Error("extension unavailable"));

        service.open(createTokenFeed(), "axiom", "current_axiom_tab");
        await Promise.resolve();

        expect(open).not.toHaveBeenCalled();
        expect(consoleError).toHaveBeenCalledOnce();
        consoleError.mockRestore();
    });
});
