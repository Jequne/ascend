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

export async function navigateWithAxiomHistory(url: string): Promise<boolean> {
    const validation = validateAxiomTokenUrl(url);
    if (!validation.ok) return false;

    const monitor = monitorAxiomRender(validation.url, document.title);
    const acknowledged = await requestMainWorldNavigation(validation.url);
    if (!acknowledged) {
        monitor.cancel();
        return false;
    }
    return monitor.result;
}

function requestMainWorldNavigation(url: string): Promise<boolean> {
    const requestId = crypto.randomUUID();
    return new Promise((resolve) => {
        const finish = (result: boolean) => {
            clearTimeout(timeout);
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
        const timeout = setTimeout(() => finish(false), BRIDGE_TIMEOUT_MS);

        window.addEventListener(AXIOM_NAVIGATION_RESULT_EVENT, handleResponse);
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
): { result: Promise<boolean>; cancel: () => void } {
    let finish: (result: boolean) => void = () => undefined;
    let observedBusyState = false;
    let settled = false;

    const observer = new MutationObserver((records) => {
        observedBusyState ||= records.some(recordContainsBusyState);
        check();
    });
    const result = new Promise<boolean>((resolve) => {
        finish = (value) => {
            if (settled) return;
            settled = true;
            observer.disconnect();
            clearTimeout(timeout);
            resolve(value);
        };
    });
    const check = () => {
        if (
            window.location.href === targetUrl &&
            observedBusyState &&
            !document.querySelector(BUSY_SELECTOR) &&
            document.title !== previousTitle
        ) {
            finish(true);
        }
    };
    const timeout = setTimeout(() => finish(false), RENDER_TIMEOUT_MS);

    observer.observe(document.documentElement, {
        subtree: true,
        childList: true,
        characterData: true,
        attributes: true,
        attributeFilter: ["aria-busy", "role"],
    });

    return { result, cancel: () => finish(false) };
}

function recordContainsBusyState(record: MutationRecord): boolean {
    if (
        record.type === "attributes" &&
        record.target instanceof Element &&
        record.target.matches(BUSY_SELECTOR)
    ) {
        return true;
    }
    return [...record.addedNodes].some(
        (node) =>
            node instanceof Element &&
            (node.matches(BUSY_SELECTOR) ||
                node.querySelector(BUSY_SELECTOR) !== null),
    );
}
