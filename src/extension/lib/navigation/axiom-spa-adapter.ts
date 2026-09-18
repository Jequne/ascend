import { validateAxiomTokenUrl } from "./axiom-url";
import {
    AXIOM_NAVIGATE_EVENT,
    AXIOM_NAVIGATION_RESULT_EVENT,
    parseMainWorldResponse,
    serializeMainWorldMessage,
} from "./axiom-main-world-protocol";

const BRIDGE_TIMEOUT_MS = 1_000;

export async function navigateWithAxiomHistory(
    url: string,
    signal?: AbortSignal,
): Promise<boolean> {
    const validation = validateAxiomTokenUrl(url);
    if (!validation.ok || signal?.aborted) return false;

    return requestMainWorldNavigation(validation.url, signal);
}

function requestMainWorldNavigation(
    url: string,
    signal?: AbortSignal,
): Promise<boolean> {
    const requestId = crypto.randomUUID();
    return new Promise((resolve) => {
        const finish = (result: boolean) => {
            clearTimeout(timeout);
            signal?.removeEventListener("abort", handleAbort);
            window.removeEventListener(
                AXIOM_NAVIGATION_RESULT_EVENT,
                handleResponse,
            );
            resolve(result);
        };
        const handleResponse = (event: Event) => {
            if (!(event instanceof CustomEvent)) return;
            const response = parseMainWorldResponse(event.detail);
            if (!response || response.requestId !== requestId) return;
            finish(response.ok);
        };
        const handleAbort = () => finish(false);
        const timeout = setTimeout(() => finish(false), BRIDGE_TIMEOUT_MS);

        window.addEventListener(AXIOM_NAVIGATION_RESULT_EVENT, handleResponse);
        signal?.addEventListener("abort", handleAbort, { once: true });
        if (signal?.aborted) {
            finish(false);
            return;
        }
        window.dispatchEvent(
            new CustomEvent(AXIOM_NAVIGATE_EVENT, {
                detail: serializeMainWorldMessage({ requestId, url }),
            }),
        );
    });
}
