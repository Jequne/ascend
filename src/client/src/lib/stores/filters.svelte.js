import { DEFAULT_FILTERS } from "$lib/config/constants.js";

class FiltersStore {
    minDevHoldsPercent = $state(DEFAULT_FILTERS.minDevHoldsPercent);
    maxDevHoldsPercent = $state(DEFAULT_FILTERS.maxDevHoldsPercent);
    minMigrationPercent = $state(DEFAULT_FILTERS.minMigrationPercent);
}

export const filtersStore = new FiltersStore();