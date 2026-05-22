import { DEFAULT_FILTERS } from "$lib/config/constants.js";

class FiltersStore {
    minDevHoldsPercent = $state(DEFAULT_FILTERS.minDevHoldsPercent);
    maxDevHoldsPercent = $state(DEFAULT_FILTERS.maxDevHoldsPercent);
    minMigrationPercent = $state(DEFAULT_FILTERS.minMigrationPercent);
    feesMode = $state(DEFAULT_FILTERS.feesMode);
    minLastTokenFees = $state(DEFAULT_FILTERS.minLastTokenFees);
    terminal = $state(DEFAULT_FILTERS.terminal);
}

export const filtersStore = new FiltersStore();