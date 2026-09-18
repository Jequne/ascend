import { validateAxiomTokenUrl } from "./axiom-url";
import {
    AXIOM_NAVIGATE_EVENT,
    AXIOM_NAVIGATION_RESULT_EVENT,
    parseMainWorldResponse,
    serializeMainWorldMessage,
} from "./axiom-main-world-protocol";

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
        let settled = false;
        const finish = (result: boolean) => {
            if (settled) return;
            settled = true;
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
        if (!settled) finish(window.location.href === url);
    });
}
