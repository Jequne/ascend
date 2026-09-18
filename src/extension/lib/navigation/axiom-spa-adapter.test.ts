import { afterEach, describe, expect, it } from "vitest";
import {
    AXIOM_NAVIGATE_EVENT,
    AXIOM_NAVIGATION_RESULT_EVENT,
    parseMainWorldRequest,
    serializeMainWorldMessage,
} from "./axiom-main-world-protocol";
import { navigateWithAxiomHistory } from "./axiom-spa-adapter";

const targetUrl = "https://axiom.trade/meme/pair?chain=sol";

let removeNavigationListener: (() => void) | undefined;

afterEach(() => {
    removeNavigationListener?.();
    removeNavigationListener = undefined;
    document.title = "Axiom";
});

describe("Axiom SPA adapter", () => {
    it("stops waiting for an obsolete render when navigation is aborted", async () => {
        installAcknowledgingMainWorld();
        const controller = new AbortController();
        const navigation = navigateWithAxiomHistory(
            targetUrl,
            controller.signal,
        );

        controller.abort();

        await expect(navigation).resolves.toBe(false);
    });
});

function installAcknowledgingMainWorld(): void {
    const handleNavigation = (event: Event) => {
        if (!(event instanceof CustomEvent)) return;
        const request = parseMainWorldRequest(event.detail);
        if (!request) return;
        window.dispatchEvent(
            new CustomEvent(AXIOM_NAVIGATION_RESULT_EVENT, {
                detail: serializeMainWorldMessage({
                    requestId: request.requestId,
                    ok: true,
                }),
            }),
        );
    };
    window.addEventListener(AXIOM_NAVIGATE_EVENT, handleNavigation);
    removeNavigationListener = () =>
        window.removeEventListener(AXIOM_NAVIGATE_EVENT, handleNavigation);
}
