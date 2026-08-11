import { isPlainObject } from "$lib/config/settings";
import type {
    LastDeployedToken,
    TokenFeedPayload,
    WebSocketMessage,
} from "$lib/types";

const isString = (value: unknown): value is string => typeof value === "string";
const isNumber = (value: unknown): value is number =>
    typeof value === "number" && Number.isFinite(value);
const isBoolean = (value: unknown): value is boolean =>
    typeof value === "boolean";
const isNullableString = (value: unknown): value is string | null =>
    value === null || isString(value);
const isNullableNumber = (value: unknown): value is number | null =>
    value === null || isNumber(value);

function hasStringFields(
    value: Record<string, unknown>,
    fields: readonly string[],
): boolean {
    return fields.every((field) => isString(value[field]));
}

function hasNullableStringFields(
    value: Record<string, unknown>,
    fields: readonly string[],
): boolean {
    return fields.every((field) => isNullableString(value[field]));
}

export function isLastDeployedToken(
    value: unknown,
): value is LastDeployedToken {
    if (!isPlainObject(value)) return false;

    return (
        hasStringFields(value, [
            "blockchain",
            "pair_address",
            "token_address",
            "token_name",
            "token_ticker",
            "dev_wallet",
            "protocol",
            "created_at",
        ]) &&
        hasNullableStringFields(value, [
            "token_image",
            "website",
            "telegram",
            "discord",
            "twitter",
            "twitter_admin_nickname",
            "twitter_admin_id",
        ]) &&
        isNumber(value.total_pair_fees_paid) &&
        isNullableNumber(value.ath_mcap_in_usd) &&
        isBoolean(value.dex_paid) &&
        isBoolean(value.is_migrated)
    );
}

export function isTokenFeedPayload(value: unknown): value is TokenFeedPayload {
    if (!isPlainObject(value)) return false;

    return (
        (value.blockchain === "sol" || value.blockchain === "bsc") &&
        hasStringFields(value, [
            "indicator",
            "pair_address",
            "token_address",
            "token_name",
            "token_ticker",
            "dev_wallet",
            "protocol",
        ]) &&
        hasNullableStringFields(value, [
            "token_image",
            "website",
            "telegram",
            "discord",
            "twitter",
            "twitter_admin_nickname",
            "twitter_admin_id",
        ]) &&
        isNullableNumber(value.dev_holds_percent) &&
        isNullableNumber(value.snipers_hold_percent) &&
        isBoolean(value.is_migrated) &&
        isNumber(value.migrated_tokens_count) &&
        isNumber(value.all_tokens_count) &&
        (value.last_deployed_tokens === null ||
            (Array.isArray(value.last_deployed_tokens) &&
                value.last_deployed_tokens.every(isLastDeployedToken)))
    );
}

export function isWebSocketMessage(value: unknown): value is WebSocketMessage {
    if (!isPlainObject(value)) return false;

    if (value.type === "ping") {
        return (
            isPlainObject(value.payload) && isString(value.payload.timestamp)
        );
    }

    if (value.type === "sol_price") {
        return isNumber(value.payload) || isString(value.payload);
    }

    return value.type === "token_feed" && isTokenFeedPayload(value.payload);
}

export function parseWebSocketMessage(
    rawData: unknown,
): WebSocketMessage | null {
    if (typeof rawData !== "string") return null;

    try {
        const parsed: unknown = JSON.parse(rawData);
        return isWebSocketMessage(parsed) ? parsed : null;
    } catch {
        return null;
    }
}
