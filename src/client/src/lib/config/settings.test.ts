import { describe, expect, it } from "vitest";
import { DEFAULT_FILTERS } from "$lib/config/constants";
import {
    SETTINGS_EXPORT_SCHEMA,
    SETTINGS_EXPORT_SCHEMA_VERSION,
    createSettingsExportPayload,
    normalizeFilters,
    parseSettingsImport,
} from "$lib/config/settings";

const legacyFilters = {
    ...DEFAULT_FILTERS,
    minMigrationPercent: 42,
    aggressiveAutoOpen: true,
};

describe("settings import compatibility", () => {
    it("normalizes numeric bounds, modes, terminal, blacklist, and booleans", () => {
        expect(
            normalizeFilters({
                minDevHoldsPercent: 90,
                maxDevHoldsPercent: 10,
                minMigrationPercent: 120,
                feesMode: "unsupported",
                minLastTokenFees: -1,
                minLastTokenAthMcap: "250000",
                lastTokensRequiredCount: 2.6,
                blacklist: [" Wallet ", "wallet", "Token"],
                terminal: "unsupported",
                autoOpenInNewTab: "false",
                highlightMigratedTokens: false,
            }),
        ).toEqual({
            minDevHoldsPercent: 10,
            maxDevHoldsPercent: 90,
            minMigrationPercent: 100,
            feesMode: DEFAULT_FILTERS.feesMode,
            minLastTokenFees: 0,
            minLastTokenAthMcap: 250_000,
            lastTokensRequiredCount: 3,
            blacklist: ["Wallet", "Token"],
            terminal: DEFAULT_FILTERS.terminal,
            autoOpenInNewTab: false,
            highlightMigratedTokens: false,
        });
    });

    it("exports schema v2 without the retired aggressive mode", () => {
        const exported = createSettingsExportPayload({
            filters: legacyFilters,
        });

        expect(exported.schemaVersion).toBe(SETTINGS_EXPORT_SCHEMA_VERSION);
        expect(exported.schemaVersion).toBe(2);
        expect(exported.settings.filters).not.toHaveProperty(
            "aggressiveAutoOpen",
        );
    });

    it.each([
        {
            name: "v2 envelope",
            input: {
                schema: SETTINGS_EXPORT_SCHEMA,
                schemaVersion: 2,
                exportedAt: "2026-08-11T00:00:00.000Z",
                settings: { filters: legacyFilters },
            },
        },
        {
            name: "v1 envelope",
            input: {
                schema: SETTINGS_EXPORT_SCHEMA,
                schemaVersion: 1,
                exportedAt: "2026-08-11T00:00:00.000Z",
                settings: { filters: legacyFilters },
            },
        },
        {
            name: "legacy flat settings",
            input: legacyFilters,
        },
    ])("imports $name and silently removes aggressive mode", ({ input }) => {
        const imported = parseSettingsImport(JSON.stringify(input));

        expect(imported.filters.minMigrationPercent).toBe(42);
        expect(imported.filters).not.toHaveProperty("aggressiveAutoOpen");
    });

    it("rejects malformed JSON and unsupported envelopes", () => {
        expect(() => parseSettingsImport("{")).toThrow();
        expect(() =>
            parseSettingsImport({
                schema: "another.settings",
                schemaVersion: 2,
                settings: { filters: DEFAULT_FILTERS },
            }),
        ).toThrow("Unsupported settings schema.");
        expect(() =>
            parseSettingsImport({
                schema: SETTINGS_EXPORT_SCHEMA,
                schemaVersion: 3,
                settings: { filters: DEFAULT_FILTERS },
            }),
        ).toThrow("Unsupported settings schema version.");
    });
});
