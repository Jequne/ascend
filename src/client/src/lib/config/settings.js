import { DEFAULT_FILTERS } from "$lib/config/constants.js";

export const SETTINGS_STORAGE_KEY = "ascend_trenches.user_settings";
export const SETTINGS_EXPORT_SCHEMA = "ascend_trenches.settings";
export const SETTINGS_EXPORT_SCHEMA_VERSION = 1;
export const SETTINGS_EXPORT_FILENAME = "ascend-trenches-settings.json";

const ALLOWED_FEES_MODES = new Set(["avg", "total", "fixed"]);
const ALLOWED_TERMINALS = new Set(["axiom", "gmgn"]);

function isPlainObject(value) {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function cloneObject(value) {
    return isPlainObject(value) ? { ...value } : {};
}

function clampNumber(value, min, max, fallback) {
    const numericValue = Number(value);
    if (!Number.isFinite(numericValue)) return fallback;
    return Math.min(max, Math.max(min, numericValue));
}

function normalizeFeesMode(value) {
    return ALLOWED_FEES_MODES.has(value) ? value : DEFAULT_FILTERS.feesMode;
}

function normalizeTerminal(value) {
    return ALLOWED_TERMINALS.has(value) ? value : DEFAULT_FILTERS.terminal;
}

export function normalizeFilters(filters = {}) {
    const source = isPlainObject(filters) ? filters : {};
    const minDev = clampNumber(
        source.minDevHoldsPercent,
        0,
        100,
        DEFAULT_FILTERS.minDevHoldsPercent,
    );
    const maxDev = clampNumber(
        source.maxDevHoldsPercent,
        0,
        100,
        DEFAULT_FILTERS.maxDevHoldsPercent,
    );
    const minMigrationPercent = clampNumber(
        source.minMigrationPercent,
        0,
        100,
        DEFAULT_FILTERS.minMigrationPercent,
    );
    const minLastTokenAthMcap = Math.max(
        0,
        clampNumber(
            source.minLastTokenAthMcap,
            0,
            Number.POSITIVE_INFINITY,
            DEFAULT_FILTERS.minLastTokenAthMcap,
        ),
    );
    const lastTokensRequiredCount = Math.max(
        0,
        Math.min(
            3,
            Math.round(
                clampNumber(
                    source.lastTokensRequiredCount,
                    0,
                    3,
                    DEFAULT_FILTERS.lastTokensRequiredCount,
                ),
            ),
        ),
    );

    return {
        minDevHoldsPercent: Math.min(minDev, maxDev),
        maxDevHoldsPercent: Math.max(minDev, maxDev),
        minMigrationPercent,
        feesMode: normalizeFeesMode(source.feesMode),
        minLastTokenFees: Math.max(
            0,
            clampNumber(
                source.minLastTokenFees,
                0,
                Number.POSITIVE_INFINITY,
                DEFAULT_FILTERS.minLastTokenFees,
            ),
        ),
        minLastTokenAthMcap,
        lastTokensRequiredCount,
        terminal: normalizeTerminal(source.terminal),
    };
}

export function cloneDefaultSettings() {
    return {
        filters: normalizeFilters(DEFAULT_FILTERS),
    };
}

function looksLikeLegacyFilters(candidate) {
    if (!isPlainObject(candidate)) return false;

    return [
        "minDevHoldsPercent",
        "maxDevHoldsPercent",
        "minMigrationPercent",
        "feesMode",
        "minLastTokenFees",
        "minLastTokenAthMcap",
        "lastTokensRequiredCount",
        "terminal",
    ].some((key) => Object.prototype.hasOwnProperty.call(candidate, key));
}

function extractSections(candidate) {
    if (!isPlainObject(candidate)) return null;

    if (isPlainObject(candidate.settings)) return candidate.settings;
    if (isPlainObject(candidate.sections)) return candidate.sections;
    if (isPlainObject(candidate.payload)) return candidate.payload;
    if (Object.prototype.hasOwnProperty.call(candidate, "filters")) {
        return candidate;
    }
    if (looksLikeLegacyFilters(candidate)) {
        return {
            filters: candidate,
        };
    }

    return null;
}

export function normalizeSettingsSections(candidate) {
    const sections = extractSections(candidate) ?? {};
    return {
        filters: normalizeFilters(sections.filters),
    };
}

export function createSettingsExportPayload(sections) {
    return {
        schema: SETTINGS_EXPORT_SCHEMA,
        schemaVersion: SETTINGS_EXPORT_SCHEMA_VERSION,
        exportedAt: new Date().toISOString(),
        settings: normalizeSettingsSections(sections),
    };
}

export function parseSettingsImport(rawInput) {
    const parsed =
        typeof rawInput === "string" ? JSON.parse(rawInput) : rawInput;

    if (!isPlainObject(parsed)) {
        throw new Error("Settings file must contain a JSON object.");
    }

    const isExportEnvelope =
        parsed.schema === SETTINGS_EXPORT_SCHEMA ||
        Object.prototype.hasOwnProperty.call(parsed, "settings") ||
        Object.prototype.hasOwnProperty.call(parsed, "sections") ||
        Object.prototype.hasOwnProperty.call(parsed, "payload");

    if (!isExportEnvelope && !looksLikeLegacyFilters(parsed)) {
        throw new Error("The selected file does not look like a settings export.");
    }

    return normalizeSettingsSections(parsed);
}

export function readStoredSettings() {
    if (typeof localStorage === "undefined") return null;

    try {
        const rawValue = localStorage.getItem(SETTINGS_STORAGE_KEY);
        if (!rawValue) return null;
        return parseSettingsImport(rawValue);
    } catch (error) {
        console.error("Failed to read stored settings:", error);
        return null;
    }
}

export function writeStoredSettings(sections) {
    if (typeof localStorage === "undefined") return false;

    try {
        localStorage.setItem(
            SETTINGS_STORAGE_KEY,
            JSON.stringify(createSettingsExportPayload(sections)),
        );
        return true;
    } catch (error) {
        console.error("Failed to persist settings:", error);
        return false;
    }
}

export function cloneSection(value) {
    if (typeof structuredClone === "function") {
        return structuredClone(value);
    }

    return cloneObject(JSON.parse(JSON.stringify(value)));
}