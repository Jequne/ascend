import { describe, expect, it } from "vitest";
import { DEFAULT_FILTERS } from "$lib/config/constants";
import {
    SETTINGS_EXPORT_SCHEMA,
    SETTINGS_EXPORT_SCHEMA_VERSION,
    createSettingsExportPayload,
    normalizeFilters,
    parseSettingsImport,
} from "$lib/config/settings";

const legacyDefaults = Object.fromEntries(
    Object.entries(DEFAULT_FILTERS).filter(([key]) => key !== "autoOpenMode"),
);
const legacyFilters = {
    ...legacyDefaults,
    minMigrationPercent: 42,
    autoOpenInNewTab: true,
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
                autoOpenMode: "unsupported",
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
            autoOpenMode: "off",
            highlightMigratedTokens: false,
        });
    });

    it("exports schema v3 without the legacy boolean", () => {
        const exported = createSettingsExportPayload({
            filters: {
                ...DEFAULT_FILTERS,
                autoOpenMode: "current_axiom_tab",
                autoOpenInNewTab: true,
            },
        });

        expect(exported.schemaVersion).toBe(SETTINGS_EXPORT_SCHEMA_VERSION);
        expect(exported.schemaVersion).toBe(3);
        expect(exported.settings.filters.autoOpenMode).toBe(
            "current_axiom_tab",
        );
        expect(exported.settings.filters).not.toHaveProperty(
            "autoOpenInNewTab",
        );
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
        { name: "legacy flat settings", input: legacyFilters },
    ])("migrates $name to new_tab", ({ input }) => {
        const imported = parseSettingsImport(JSON.stringify(input));

        expect(imported.filters.minMigrationPercent).toBe(42);
        expect(imported.filters.autoOpenMode).toBe("new_tab");
        expect(imported.filters).not.toHaveProperty("autoOpenInNewTab");
        expect(imported.filters).not.toHaveProperty("aggressiveAutoOpen");
    });

    it("preserves every v3 mode and normalizes an unknown mode to off", () => {
        for (const autoOpenMode of [
            "off",
            "new_tab",
            "current_axiom_tab",
        ] as const) {
            const imported = parseSettingsImport(
                createSettingsExportPayload({
                    filters: { ...DEFAULT_FILTERS, autoOpenMode },
                }),
            );
            expect(imported.filters.autoOpenMode).toBe(autoOpenMode);
        }
        expect(
            parseSettingsImport({
                schema: SETTINGS_EXPORT_SCHEMA,
                schemaVersion: 3,
                settings: {
                    filters: { ...DEFAULT_FILTERS, autoOpenMode: "surprise" },
                },
            }).filters.autoOpenMode,
        ).toBe("off");
    });

    it("rejects malformed JSON and unsupported envelopes", () => {
        expect(() => parseSettingsImport("{")).toThrow();
        expect(() =>
            parseSettingsImport({
                schema: "another.settings",
                schemaVersion: 3,
                settings: { filters: DEFAULT_FILTERS },
            }),
        ).toThrow("Unsupported settings schema.");
        expect(() =>
            parseSettingsImport({
                schema: SETTINGS_EXPORT_SCHEMA,
                schemaVersion: 4,
                settings: { filters: DEFAULT_FILTERS },
            }),
        ).toThrow("Unsupported settings schema version.");
    });
});
