export const AXIOM_NAVIGATE_EVENT = "ascend-ext:axiom-navigate:v1";
export const AXIOM_NAVIGATION_RESULT_EVENT =
    "ascend-ext:axiom-navigation-result:v1";

export type AxiomMainWorldRequest = {
    requestId: string;
    url: string;
};

export type AxiomMainWorldResponse = {
    requestId: string;
    ok: boolean;
};

export function serializeMainWorldMessage(
    value: AxiomMainWorldRequest | AxiomMainWorldResponse,
): string {
    return JSON.stringify(value);
}

export function parseMainWorldRequest(
    value: unknown,
): AxiomMainWorldRequest | null {
    const parsed = parseSerializedRecord(value);
    if (
        !parsed ||
        !isUuid(parsed.requestId) ||
        typeof parsed.url !== "string"
    ) {
        return null;
    }
    return { requestId: parsed.requestId, url: parsed.url };
}

export function parseMainWorldResponse(
    value: unknown,
): AxiomMainWorldResponse | null {
    const parsed = parseSerializedRecord(value);
    if (
        !parsed ||
        !isUuid(parsed.requestId) ||
        typeof parsed.ok !== "boolean"
    ) {
        return null;
    }
    return { requestId: parsed.requestId, ok: parsed.ok };
}

function parseSerializedRecord(value: unknown): Record<string, unknown> | null {
    if (typeof value !== "string") return null;
    try {
        const parsed: unknown = JSON.parse(value);
        return typeof parsed === "object" &&
            parsed !== null &&
            !Array.isArray(parsed)
            ? (parsed as Record<string, unknown>)
            : null;
    } catch {
        return null;
    }
}

function isUuid(value: unknown): value is string {
    return (
        typeof value === "string" &&
        /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
            value,
        )
    );
}
