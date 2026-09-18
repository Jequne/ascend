import { validateAxiomTokenUrl } from "../navigation/axiom-url";
import type { DesktopBridgeMessage } from "../types/bridge";

export function parseDesktopBridgeMessage(
    raw: unknown,
): DesktopBridgeMessage | null {
    if (typeof raw !== "string" || raw.length > 16 * 1024) return null;

    let value: unknown;
    try {
        value = JSON.parse(raw) as unknown;
    } catch {
        return null;
    }
    if (
        !isRecord(value) ||
        value.protocolVersion !== 1 ||
        typeof value.type !== "string"
    ) {
        return null;
    }

    if (
        value.type === "state" &&
        isAutoOpenMode(value.mode) &&
        value.bridgeStatus === "ready" &&
        hasOnlyKeys(value, ["type", "protocolVersion", "mode", "bridgeStatus"])
    ) {
        return value as DesktopBridgeMessage;
    }
    if (
        value.type === "navigate" &&
        isUuid(value.commandId) &&
        typeof value.url === "string" &&
        validateAxiomTokenUrl(value.url).ok &&
        isIsoDate(value.issuedAt) &&
        hasOnlyKeys(value, [
            "type",
            "protocolVersion",
            "commandId",
            "url",
            "issuedAt",
        ])
    ) {
        return value as DesktopBridgeMessage;
    }
    if (
        value.type === "mode_result" &&
        isUuid(value.requestId) &&
        typeof value.accepted === "boolean" &&
        isAutoOpenMode(value.mode) &&
        (value.errorCode === undefined ||
            typeof value.errorCode === "string") &&
        hasOnlyKeys(value, [
            "type",
            "protocolVersion",
            "requestId",
            "accepted",
            "mode",
            "errorCode",
        ])
    ) {
        return value as DesktopBridgeMessage;
    }
    if (
        value.type === "pong" &&
        isIsoDate(value.sentAt) &&
        hasOnlyKeys(value, ["type", "protocolVersion", "sentAt"])
    ) {
        return value as DesktopBridgeMessage;
    }
    return null;
}

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasOnlyKeys(
    value: Record<string, unknown>,
    allowed: readonly string[],
): boolean {
    const allowedKeys = new Set(allowed);
    return Object.keys(value).every((key) => allowedKeys.has(key));
}

function isAutoOpenMode(value: unknown): boolean {
    return (
        value === "off" || value === "new_tab" || value === "current_axiom_tab"
    );
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
