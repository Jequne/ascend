import { DEFAULT_FILTERS } from "$lib/config/constants";
import {
    SETTINGS_EXPORT_FILENAME,
    normalizeFilters,
} from "$lib/config/settings";
import { settingsStore } from "$lib/stores/settings.svelte";
import type {
    BlacklistMatcher,
    FeesMode,
    FilterSnapshot,
    FilterSettings,
    Terminal,
} from "$lib/types";
import { createBlacklistMatcher } from "$lib/utils/blacklist";

class FiltersStore {
    private snapshotSource: FilterSettings | null = null;
    private snapshotCache: FilterSnapshot | null = null;

    get filters(): FilterSettings {
        return settingsStore.getSection("filters") ?? DEFAULT_FILTERS;
    }

    get minDevHoldsPercent(): number {
        return this.filters.minDevHoldsPercent;
    }

    set minDevHoldsPercent(value: number) {
        this.updateFilters({ minDevHoldsPercent: value });
    }

    get maxDevHoldsPercent(): number {
        return this.filters.maxDevHoldsPercent;
    }

    set maxDevHoldsPercent(value: number) {
        this.updateFilters({ maxDevHoldsPercent: value });
    }

    get minMigrationPercent(): number {
        return this.filters.minMigrationPercent;
    }

    set minMigrationPercent(value: number) {
        this.updateFilters({ minMigrationPercent: value });
    }

    get feesMode(): FeesMode {
        return this.filters.feesMode;
    }

    set feesMode(value: FeesMode) {
        this.updateFilters({ feesMode: value });
    }

    get minLastTokenFees(): number {
        return this.filters.minLastTokenFees;
    }

    set minLastTokenFees(value: number) {
        this.updateFilters({ minLastTokenFees: value });
    }

    get minLastTokenAthMcap(): number {
        return this.filters.minLastTokenAthMcap;
    }

    set minLastTokenAthMcap(value: number) {
        this.updateFilters({ minLastTokenAthMcap: value });
    }

    get lastTokensRequiredCount(): number {
        return this.filters.lastTokensRequiredCount;
    }

    set lastTokensRequiredCount(value: number) {
        this.updateFilters({ lastTokensRequiredCount: value });
    }

    get blacklist(): string[] {
        return this.filters.blacklist;
    }

    set blacklist(value: string[]) {
        this.updateFilters({ blacklist: value });
    }

    get blacklistMatcher(): BlacklistMatcher | null {
        return this.snapshot.blacklistMatcher;
    }

    get terminal(): Terminal {
        return this.filters.terminal;
    }

    set terminal(value: Terminal) {
        this.updateFilters({ terminal: value });
    }

    get autoOpenInNewTab(): boolean {
        return this.filters.autoOpenInNewTab;
    }

    set autoOpenInNewTab(value: boolean) {
        this.updateFilters({ autoOpenInNewTab: value });
    }

    get snapshot(): FilterSnapshot {
        const filters = this.filters;

        if (this.snapshotSource === filters && this.snapshotCache) {
            return this.snapshotCache;
        }

        const normalizedFilters = normalizeFilters(filters);
        const frozenFilters = Object.freeze({
            ...normalizedFilters,
            blacklist: Object.freeze([...normalizedFilters.blacklist]),
        });
        const snapshot: FilterSnapshot = Object.freeze({
            filters: frozenFilters,
            blacklistMatcher: createBlacklistMatcher(frozenFilters.blacklist),
        });
        this.snapshotSource = filters;
        this.snapshotCache = snapshot;

        return snapshot;
    }

    init(): void {
        settingsStore.init();
        void this.snapshot;
    }

    updateFilters(partialFilters: Partial<FilterSettings>): void {
        const nextFilters = normalizeFilters({
            ...this.filters,
            ...partialFilters,
        });
        settingsStore.setSection("filters", nextFilters);
        void this.snapshot;
    }

    resetToDefaults(): void {
        this.updateFilters(DEFAULT_FILTERS);
    }

    exportToJson(): string {
        return settingsStore.exportToJson();
    }

    importFromJson(rawJson: string): FilterSettings {
        const filters = settingsStore.importFromJson(rawJson).filters;
        void this.snapshot;
        return filters;
    }

    exportFileName(): string {
        return SETTINGS_EXPORT_FILENAME;
    }
}

export const filtersStore = new FiltersStore();
