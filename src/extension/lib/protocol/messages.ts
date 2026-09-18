import type { NavigateCommand, NavigationResult } from "../types/navigation";
import type { PopupSnapshot } from "../types/popup";
import { isAxiomPageUrl } from "../navigation/axiom-url";

export type InternalRequest =
    | { type: "get_popup_state" }
    | { type: "start_target" }
    | { type: "stop_target" }
    | { type: "pair_bridge"; pairingCode: string }
    | { type: "retry_bridge" }
    | ({ type: "navigate_target" } & NavigateCommand);

export type InternalResponse =
    | { type: "popup_state"; state: PopupSnapshot }
    | {
          type: "action_result";
          ok: true;
          state: PopupSnapshot;
      }
    | {
          type: "action_result";
          ok: false;
          errorCode: string;
          state: PopupSnapshot;
      }
    | { type: "navigation_result"; result: NavigationResult }
    | { type: "invalid_request"; errorCode: "invalid_message" };

export type ContentNavigateRequest = {
    type: "content_navigate";
    commandId: string;
    url: string;
};

export function parseInternalRequest(value: unknown): InternalRequest | null {
    if (!isRecord(value) || typeof value.type !== "string") return null;

    if (
        value.type === "get_popup_state" ||
        value.type === "start_target" ||
        value.type === "stop_target" ||
        value.type === "retry_bridge"
    ) {
        return { type: value.type };
    }

    if (value.type === "pair_bridge" && typeof value.pairingCode === "string") {
        return { type: value.type, pairingCode: value.pairingCode };
    }

    if (
        value.type === "navigate_target" &&
        isUuid(value.commandId) &&
        typeof value.url === "string" &&
        isIsoDate(value.issuedAt)
    ) {
        return {
            type: value.type,
            commandId: value.commandId,
            url: value.url,
            issuedAt: value.issuedAt,
        };
    }

    return null;
}

export function parseContentNavigateRequest(
    value: unknown,
): ContentNavigateRequest | null {
    if (
        !isRecord(value) ||
        value.type !== "content_navigate" ||
        !isUuid(value.commandId) ||
        typeof value.url !== "string"
    ) {
        return null;
    }

    return {
        type: value.type,
        commandId: value.commandId,
        url: value.url,
    };
}

export function isInternalResponse(value: unknown): value is InternalResponse {
    if (!isRecord(value) || typeof value.type !== "string") return false;
    if (value.type === "popup_state") return isPopupSnapshot(value.state);
    if (value.type === "navigation_result") {
        return parseNavigationResult(value.result) !== null;
    }
    if (value.type === "invalid_request") {
        return value.errorCode === "invalid_message";
    }
    if (value.type !== "action_result" || !isPopupSnapshot(value.state)) {
        return false;
    }
    return (
        value.ok === true ||
        (value.ok === false && typeof value.errorCode === "string")
    );
}

export function parseNavigationResult(value: unknown): NavigationResult | null {
    if (
        !isRecord(value) ||
        !isUuid(value.commandId) ||
        (value.status !== "completed" &&
            value.status !== "superseded" &&
            value.status !== "ignored" &&
            value.status !== "failed") ||
        (value.method !== undefined && value.method !== "history") ||
        (value.errorCode !== undefined && typeof value.errorCode !== "string")
    ) {
        return null;
    }

    return {
        commandId: value.commandId,
        status: value.status,
        ...(value.method === undefined ? {} : { method: value.method }),
        ...(value.errorCode === undefined
            ? {}
            : { errorCode: value.errorCode }),
    };
}

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isPopupSnapshot(value: unknown): value is PopupSnapshot {
    if (
        !isRecord(value) ||
        !isRecord(value.activePage) ||
        !isRecord(value.target)
    ) {
        return false;
    }

    const activePageValid =
        value.activePage.kind === "other" ||
        value.activePage.kind === "unavailable" ||
        (value.activePage.kind === "axiom" &&
            Number.isInteger(value.activePage.tabId) &&
            typeof value.activePage.title === "string" &&
            isAxiomPageUrl(value.activePage.url));
    const targetValid =
        value.target.kind === "idle" ||
        (value.target.kind === "running" &&
            Number.isInteger(value.target.tabId) &&
            typeof value.target.title === "string" &&
            isAxiomPageUrl(value.target.url)) ||
        (value.target.kind === "paused" &&
            (value.target.reason === "target_closed" ||
                value.target.reason === "target_left_axiom" ||
                value.target.reason === "target_missing"));
    const bridgeValid =
        isRecord(value.bridge) &&
        (value.bridge.connection === "unpaired" ||
            value.bridge.connection === "connecting" ||
            value.bridge.connection === "connected" ||
            value.bridge.connection === "reconnecting" ||
            value.bridge.connection === "pairing_rejected" ||
            value.bridge.connection === "version_mismatch" ||
            value.bridge.connection === "unavailable") &&
        (value.bridge.mode === "off" ||
            value.bridge.mode === "new_tab" ||
            value.bridge.mode === "current_axiom_tab") &&
        Number.isInteger(value.bridge.reconnectAttempt);
    return activePageValid && targetValid && bridgeValid;
}

function isUuid(value: unknown): value is string {
    return (
        typeof value === "string" &&
        /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
            value,
        )
    );
}

function isIsoDate(value: unknown): value is string {
    return (
        typeof value === "string" &&
        Number.isFinite(Date.parse(value)) &&
        new Date(value).toISOString() === value
    );
}
