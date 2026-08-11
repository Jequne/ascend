import { DEFAULT_FILTERS } from "$lib/config/constants";
import type {
    FeesMode,
    FilterSettings,
    SettingsEnvelopeV1,
    SettingsSections,
    Terminal,
} from "$lib/types";
import { normalizeBlacklistEntries } from "$lib/utils/blacklist";

export const SETTINGS_STORAGE_KEY = "ascend_trenches.user_settings";
export const SETTINGS_EXPORT_SCHEMA = "ascend_trenches.settings";
export const SETTINGS_EXPORT_SCHEMA_VERSION = 1;
export const SETTINGS_EXPORT_FILENAME = "ascend-trenches-settings.json";

const ALLOWED_FEES_MODES = new Set<FeesMode>(["avg", "total", "fixed"]);
const ALLOWED_TERMINALS = new Set<Terminal>(["axiom", "gmgn"]);

export function isPlainObject(
    value: unknown,
): value is Record<string, unknown> {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function clampNumber(
    value: unknown,
    min: number,
    max: number,
    fallback: number,
): number {
    const numericValue = Number(value);
    if (!Number.isFinite(numericValue)) return fallback;
    return Math.min(max, Math.max(min, numericValue));
}

function normalizeFeesMode(value: unknown): FeesMode {
    return typeof value === "string" &&
        ALLOWED_FEES_MODES.has(value as FeesMode)
        ? (value as FeesMode)
        : DEFAULT_FILTERS.feesMode;
}

function normalizeTerminal(value: unknown): Terminal {
    return typeof value === "string" && ALLOWED_TERMINALS.has(value as Terminal)
        ? (value as Terminal)
        : DEFAULT_FILTERS.terminal;
}

export function normalizeFilters(filters: unknown = {}): FilterSettings {
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

    return {
        minDevHoldsPercent: Math.min(minDev, maxDev),
        maxDevHoldsPercent: Math.max(minDev, maxDev),
        minMigrationPercent: clampNumber(
            source.minMigrationPercent,
            0,
            100,
            DEFAULT_FILTERS.minMigrationPercent,
        ),
        feesMode: normalizeFeesMode(source.feesMode),
        minLastTokenFees: clampNumber(
            source.minLastTokenFees,
            0,
            Number.POSITIVE_INFINITY,
            DEFAULT_FILTERS.minLastTokenFees,
        ),
        minLastTokenAthMcap: clampNumber(
            source.minLastTokenAthMcap,
            0,
            Number.POSITIVE_INFINITY,
            DEFAULT_FILTERS.minLastTokenAthMcap,
        ),
        lastTokensRequiredCount: Math.round(
            clampNumber(
                source.lastTokensRequiredCount,
                0,
                3,
                DEFAULT_FILTERS.lastTokensRequiredCount,
            ),
        ),
        blacklist: normalizeBlacklistEntries(source.blacklist),
        terminal: normalizeTerminal(source.terminal),
        autoOpenInNewTab: Boolean(source.autoOpenInNewTab),
        aggressiveAutoOpen: Boolean(source.aggressiveAutoOpen),
    };
}

export function cloneDefaultSettings(): SettingsSections {
    return {
        filters: normalizeFilters(DEFAULT_FILTERS),
    };
}

function looksLikeLegacyFilters(candidate: unknown): boolean {
    if (!isPlainObject(candidate)) return false;

    return [
        "minDevHoldsPercent",
        "maxDevHoldsPercent",
        "minMigrationPercent",
        "feesMode",
        "minLastTokenFees",
        "minLastTokenAthMcap",
        "lastTokensRequiredCount",
        "blacklist",
        "terminal",
    ].some((key) => Object.hasOwn(candidate, key));
}

function extractSections(candidate: unknown): Record<string, unknown> | null {
    if (!isPlainObject(candidate)) return null;

    if (isPlainObject(candidate.settings)) return candidate.settings;
    if (isPlainObject(candidate.sections)) return candidate.sections;
    if (isPlainObject(candidate.payload)) return candidate.payload;
    if (Object.hasOwn(candidate, "filters")) return candidate;
    if (looksLikeLegacyFilters(candidate)) return { filters: candidate };

    return null;
}

export function normalizeSettingsSections(
    candidate: unknown,
): SettingsSections {
    const sections = extractSections(candidate) ?? {};
    return {
        filters: normalizeFilters(sections.filters),
    };
}

export function createSettingsExportPayload(
    sections: unknown,
): SettingsEnvelopeV1 {
    return {
        schema: SETTINGS_EXPORT_SCHEMA,
        schemaVersion: SETTINGS_EXPORT_SCHEMA_VERSION,
        exportedAt: new Date().toISOString(),
        settings: normalizeSettingsSections(sections),
    };
}

export function parseSettingsImport(rawInput: unknown): SettingsSections {
    const parsed =
        typeof rawInput === "string" ? JSON.parse(rawInput) : rawInput;

    if (!isPlainObject(parsed)) {
        throw new Error("Settings file must contain a JSON object.");
    }

    const isExportEnvelope =
        parsed.schema === SETTINGS_EXPORT_SCHEMA ||
        Object.hasOwn(parsed, "settings") ||
        Object.hasOwn(parsed, "sections") ||
        Object.hasOwn(parsed, "payload");

    if (!isExportEnvelope && !looksLikeLegacyFilters(parsed)) {
        throw new Error(
            "The selected file does not look like a settings export.",
        );
    }

    return normalizeSettingsSections(parsed);
}

export function readStoredSettings(): SettingsSections | null {
    if (typeof localStorage === "undefined") return null;

    try {
        const rawValue = localStorage.getItem(SETTINGS_STORAGE_KEY);
        return rawValue ? parseSettingsImport(rawValue) : null;
    } catch (error: unknown) {
        console.error("Failed to read stored settings:", error);
        return null;
    }
}

export function writeStoredSettings(sections: unknown): boolean {
    if (typeof localStorage === "undefined") return false;

    try {
        localStorage.setItem(
            SETTINGS_STORAGE_KEY,
            JSON.stringify(createSettingsExportPayload(sections)),
        );
        return true;
    } catch (error: unknown) {
        console.error("Failed to persist settings:", error);
        return false;
    }
}

export function cloneSection<T>(value: T): T {
    return structuredClone(value);
}
