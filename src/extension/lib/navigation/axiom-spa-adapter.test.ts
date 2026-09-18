import { afterEach, describe, expect, it, vi } from "vitest";
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
    vi.useRealTimers();
});

describe("Axiom SPA adapter", () => {
    it("resolves as soon as the SPA accepts navigation without waiting for render", async () => {
        vi.useFakeTimers();
        installAcknowledgingMainWorld();
        const timerCountBefore = vi.getTimerCount();

        await expect(navigateWithAxiomHistory(targetUrl)).resolves.toBe(true);

        expect(vi.getTimerCount()).toBe(timerCountBefore);
    });

    it("fails immediately without a throttled timer when the main-world bridge is missing", async () => {
        vi.useFakeTimers();
        const timerCountBefore = vi.getTimerCount();

        await expect(navigateWithAxiomHistory(targetUrl)).resolves.toBe(false);

        expect(vi.getTimerCount()).toBe(timerCountBefore);
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
