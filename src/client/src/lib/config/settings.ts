import { DEFAULT_FILTERS, DEFAULT_NOTIFICATIONS } from "$lib/config/constants";
import type {
    AutoOpenMode,
    DeveloperLabels,
    FeesMode,
    FilterSettings,
    NotificationSettings,
    SettingsEnvelopeV5,
    SettingsSections,
    Terminal,
} from "$lib/types";
import { normalizeBlacklistEntries } from "$lib/utils/blacklist";

export const SETTINGS_STORAGE_KEY = "ascend_trenches.user_settings";
export const SETTINGS_EXPORT_SCHEMA = "ascend_trenches.settings";
export const SETTINGS_EXPORT_SCHEMA_VERSION = 5;
export const SETTINGS_EXPORT_FILENAME = "ascend-trenches-settings.json";
export const SETTINGS_IMPORT_MAX_BYTES = 1_000_000;

const ALLOWED_FEES_MODES = new Set<FeesMode>(["avg", "total", "fixed"]);
const ALLOWED_TERMINALS = new Set<Terminal>(["axiom", "gmgn"]);
const ALLOWED_AUTO_OPEN_MODES = new Set<AutoOpenMode>([
    "off",
    "new_tab",
    "current_axiom_tab",
]);

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

function normalizeAutoOpenMode(
    value: unknown,
    legacyAutoOpenInNewTab: unknown,
): AutoOpenMode {
    if (
        typeof value === "string" &&
        ALLOWED_AUTO_OPEN_MODES.has(value as AutoOpenMode)
    ) {
        return value as AutoOpenMode;
    }
    return legacyAutoOpenInNewTab === true ? "new_tab" : "off";
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
        autoOpenMode: normalizeAutoOpenMode(
            source.autoOpenMode,
            source.autoOpenInNewTab,
        ),
        highlightMigratedTokens: source.highlightMigratedTokens !== false,
    };
}

export function normalizeDeveloperLabels(value: unknown): DeveloperLabels {
    if (!isPlainObject(value)) return {};

    const labels: DeveloperLabels = {};

    for (const [rawWallet, rawLabel] of Object.entries(value)) {
        const wallet = rawWallet.trim();
        const label = typeof rawLabel === "string" ? rawLabel.trim() : "";

        if (!wallet || !label) continue;
        labels[wallet] = label.slice(0, 48);
    }

    return labels;
}

export function normalizeNotifications(
    value: unknown = {},
): NotificationSettings {
    const source = isPlainObject(value) ? value : {};

    const customAudioId = normalizeCustomAudioId(source.customAudioId);
    const customAudioName = normalizeCustomAudioName(source.customAudioName);
    const usesCustomAudio = Boolean(
        source.source === "custom" && customAudioId && customAudioName,
    );

    return {
        enabled:
            typeof source.enabled === "boolean"
                ? source.enabled
                : DEFAULT_NOTIFICATIONS.enabled,
        volume: Math.round(
            clampNumber(source.volume, 0, 100, DEFAULT_NOTIFICATIONS.volume),
        ),
        source: usesCustomAudio ? "custom" : "default",
        customAudioId: usesCustomAudio ? customAudioId : null,
        customAudioName: usesCustomAudio ? customAudioName : null,
    };
}

function normalizeCustomAudioId(value: unknown): string | null {
    if (typeof value !== "string") return null;
    const id = value.trim();
    return /^[a-zA-Z0-9._-]{1,100}$/.test(id) ? id : null;
}

export function normalizeCustomAudioName(value: unknown): string | null {
    if (typeof value !== "string") return null;
    const basename = value.split(/[\\/]/).at(-1) ?? "";
    const safeName = [...basename]
        .filter((character) => {
            const code = character.charCodeAt(0);
            return code > 31 && code !== 127;
        })
        .join("")
        .trim()
        .slice(0, 120);
    return safeName || null;
}

export function cloneDefaultSettings(): SettingsSections {
    return {
        filters: normalizeFilters(DEFAULT_FILTERS),
        developerLabels: {},
        notifications: normalizeNotifications(DEFAULT_NOTIFICATIONS),
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
        "autoOpenInNewTab",
        "autoOpenMode",
        "highlightMigratedTokens",
        "aggressiveAutoOpen",
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
        developerLabels: normalizeDeveloperLabels(sections.developerLabels),
        notifications: normalizeNotifications(sections.notifications),
    };
}

export function createSettingsExportPayload(
    sections: unknown,
): SettingsEnvelopeV5 {
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

    if (
        parsed.schema !== undefined &&
        parsed.schema !== SETTINGS_EXPORT_SCHEMA
    ) {
        throw new Error("Unsupported settings schema.");
    }

    if (
        parsed.schemaVersion !== undefined &&
        ![1, 2, 3, 4, SETTINGS_EXPORT_SCHEMA_VERSION].includes(
            parsed.schemaVersion as number,
        )
    ) {
        throw new Error("Unsupported settings schema version.");
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

    const sections = normalizeSettingsSections(parsed);
    if (
        typeof parsed.schemaVersion === "number" &&
        parsed.schemaVersion < SETTINGS_EXPORT_SCHEMA_VERSION
    ) {
        sections.notifications = normalizeNotifications(DEFAULT_NOTIFICATIONS);
    }
    return sections;
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
