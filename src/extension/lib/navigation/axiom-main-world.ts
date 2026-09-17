import { isAxiomPageUrl, validateAxiomTokenUrl } from "./axiom-url";
import {
    AXIOM_NAVIGATE_EVENT,
    AXIOM_NAVIGATION_RESULT_EVENT,
    parseMainWorldRequest,
    serializeMainWorldMessage,
} from "./axiom-main-world-protocol";

type AxiomMainWorldRuntime = {
    getCurrentUrl: () => string;
    getHistoryState: () => unknown;
    pushState: (state: unknown, url: string) => void;
    dispatchPopState: (state: unknown) => void;
    sendResponse: (detail: string) => void;
};

export function installAxiomMainWorldNavigation(): () => void {
    const handleNavigation = (event: Event) => {
        if (!(event instanceof CustomEvent)) return;
        handleMainWorldNavigation(event.detail, {
            getCurrentUrl: () => window.location.href,
            getHistoryState: () => window.history.state,
            pushState: (state, url) => window.history.pushState(state, "", url),
            dispatchPopState: (state) =>
                window.dispatchEvent(new PopStateEvent("popstate", { state })),
            sendResponse: (detail) =>
                window.dispatchEvent(
                    new CustomEvent(AXIOM_NAVIGATION_RESULT_EVENT, {
                        detail,
                    }),
                ),
        });
    };

    window.addEventListener(AXIOM_NAVIGATE_EVENT, handleNavigation);
    return () =>
        window.removeEventListener(AXIOM_NAVIGATE_EVENT, handleNavigation);
}

export function handleMainWorldNavigation(
    detail: unknown,
    runtime: AxiomMainWorldRuntime,
): void {
    const request = parseMainWorldRequest(detail);
    if (!request) return;

    const validation = validateAxiomTokenUrl(request.url);
    let ok = false;

    if (isAxiomPageUrl(runtime.getCurrentUrl()) && validation.ok) {
        try {
            const state = runtime.getHistoryState();
            runtime.pushState(state, validation.url);
            runtime.dispatchPopState(state);
            ok = true;
        } catch {
            ok = false;
        }
    }

    runtime.sendResponse(
        serializeMainWorldMessage({ requestId: request.requestId, ok }),
    );
}
