import { beforeEach, describe, expect, it } from "vitest";
import { DEFAULT_FILTERS } from "$lib/config/constants";
import { filtersStore } from "$lib/stores/filters.svelte";

describe("filtersStore snapshot", () => {
    beforeEach(() => {
        filtersStore.updateFilters(DEFAULT_FILTERS);
    });

    it("reuses one immutable snapshot until normalized settings change", () => {
        const initial = filtersStore.snapshot;

        expect(filtersStore.snapshot).toBe(initial);
        expect(Object.isFrozen(initial)).toBe(true);
        expect(Object.isFrozen(initial.filters)).toBe(true);

        filtersStore.updateFilters({
            minMigrationPercent: 36,
            blacklist: [" Wallet ", "wallet", "Token"],
        });

        const updated = filtersStore.snapshot;
        expect(updated).not.toBe(initial);
        expect(updated.filters.minMigrationPercent).toBe(36);
        expect(updated.filters.blacklist).toEqual(["Wallet", "Token"]);
        expect(updated.blacklistMatcher?.matchesText("token name")).toBe(true);
        expect(filtersStore.snapshot).toBe(updated);
    });
});
