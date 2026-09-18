import { validateAxiomTokenUrl } from "./axiom-url";
import {
    AXIOM_NAVIGATE_EVENT,
    AXIOM_NAVIGATION_RESULT_EVENT,
    parseMainWorldResponse,
    serializeMainWorldMessage,
} from "./axiom-main-world-protocol";

const BRIDGE_TIMEOUT_MS = 1_000;
const RENDER_TIMEOUT_MS = 5_000;
const BUSY_SELECTOR = '[aria-busy="true"], [role="progressbar"]';

export async function navigateWithAxiomHistory(
    url: string,
    signal?: AbortSignal,
): Promise<boolean> {
    const validation = validateAxiomTokenUrl(url);
    if (!validation.ok || signal?.aborted) return false;

    const monitor = monitorAxiomRender(validation.url, document.title, signal);
    const acknowledged = await requestMainWorldNavigation(
        validation.url,
        signal,
    );
    if (!acknowledged) {
        monitor.cancel();
        return false;
    }
    return monitor.result;
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

function monitorAxiomRender(
    targetUrl: string,
    previousTitle: string,
    signal?: AbortSignal,
): { result: Promise<boolean>; cancel: () => void } {
    let finish: (result: boolean) => void = () => undefined;
    const observedBusyElements = new Set<Element>();
    let settled = false;

    const observer = new MutationObserver((records) => {
        for (const record of records) {
            collectBusyElements(record, observedBusyElements);
        }
        check();
    });
    const result = new Promise<boolean>((resolve) => {
        finish = (value) => {
            if (settled) return;
            settled = true;
            observer.disconnect();
            clearTimeout(timeout);
            signal?.removeEventListener("abort", handleAbort);
            resolve(value);
        };
    });
    const check = () => {
        if (
            window.location.href === targetUrl &&
            observedBusyElements.size > 0 &&
            [...observedBusyElements].every(
                (element) =>
                    !element.isConnected || !element.matches(BUSY_SELECTOR),
            ) &&
            document.title !== previousTitle
        ) {
            finish(true);
        }
    };
    const handleAbort = () => finish(false);
    const timeout = setTimeout(() => finish(false), RENDER_TIMEOUT_MS);

    observer.observe(document.documentElement, {
        subtree: true,
        childList: true,
        characterData: true,
        attributes: true,
        attributeFilter: ["aria-busy", "role"],
    });
    signal?.addEventListener("abort", handleAbort, { once: true });
    if (signal?.aborted) finish(false);

    return { result, cancel: () => finish(false) };
}

function collectBusyElements(
    record: MutationRecord,
    busyElements: Set<Element>,
): void {
    if (
        record.type === "attributes" &&
        record.target instanceof Element &&
        record.target.matches(BUSY_SELECTOR)
    ) {
        busyElements.add(record.target);
    }
    for (const node of record.addedNodes) {
        if (!(node instanceof Element)) continue;
        if (node.matches(BUSY_SELECTOR)) busyElements.add(node);
        for (const element of node.querySelectorAll(BUSY_SELECTOR)) {
            busyElements.add(element);
        }
    }
}
