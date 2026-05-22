import { DEFAULT_FILTERS } from "$lib/config/constants.js";
import {
    SETTINGS_EXPORT_FILENAME,
    normalizeFilters,
} from "$lib/config/settings.js";
import { settingsStore } from "$lib/stores/settings.svelte.js";

class FiltersStore {
    get filters() {
        return settingsStore.getSection("filters") ?? DEFAULT_FILTERS;
    }

    get minDevHoldsPercent() {
        return this.filters.minDevHoldsPercent;
    }

    set minDevHoldsPercent(value) {
        this.updateFilters({ minDevHoldsPercent: value });
    }

    get maxDevHoldsPercent() {
        return this.filters.maxDevHoldsPercent;
    }

    set maxDevHoldsPercent(value) {
        this.updateFilters({ maxDevHoldsPercent: value });
    }

    get minMigrationPercent() {
        return this.filters.minMigrationPercent;
    }

    set minMigrationPercent(value) {
        this.updateFilters({ minMigrationPercent: value });
    }

    get feesMode() {
        return this.filters.feesMode;
    }

    set feesMode(value) {
        this.updateFilters({ feesMode: value });
    }

    get minLastTokenFees() {
        return this.filters.minLastTokenFees;
    }

    set minLastTokenFees(value) {
        this.updateFilters({ minLastTokenFees: value });
    }

    get minLastTokenAthMcap() {
        return this.filters.minLastTokenAthMcap;
    }

    set minLastTokenAthMcap(value) {
        this.updateFilters({ minLastTokenAthMcap: value });
    }

    get lastTokensRequiredCount() {
        return this.filters.lastTokensRequiredCount;
    }

    set lastTokensRequiredCount(value) {
        this.updateFilters({ lastTokensRequiredCount: value });
    }

    get terminal() {
        return this.filters.terminal;
    }

    set terminal(value) {
        this.updateFilters({ terminal: value });
    }

    get autoOpenInNewTab() {
        return this.filters.autoOpenInNewTab;
    }

    set autoOpenInNewTab(value) {
        this.updateFilters({ autoOpenInNewTab: value });
    }

    get aggressiveAutoOpen() {
        return this.filters.aggressiveAutoOpen;
    }

    set aggressiveAutoOpen(value) {
        this.updateFilters({ aggressiveAutoOpen: value });
    }

    init() {
        settingsStore.init();
    }

    updateFilters(partialFilters) {
        const nextFilters = normalizeFilters({
            ...this.filters,
            ...(partialFilters ?? {}),
        });

        settingsStore.setSection("filters", nextFilters);
    }

    resetToDefaults() {
        settingsStore.setSection("filters", normalizeFilters(DEFAULT_FILTERS));
    }

    exportToJson() {
        return settingsStore.exportToJson();
    }

    importFromJson(rawJson) {
        const importedSettings = settingsStore.importFromJson(rawJson);
        return importedSettings.filters;
    }

    exportFileName() {
        return SETTINGS_EXPORT_FILENAME;
    }
}

export const filtersStore = new FiltersStore();