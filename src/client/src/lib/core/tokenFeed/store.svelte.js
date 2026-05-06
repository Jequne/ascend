import { DefaultFilters } from './types.js';

export function passesFilters(token, filters) {
    if (token.dev_holds_percent === null || token.dev_holds_percent === undefined) {
        if (filters.minDevHoldsPercent !== null || filters.maxDevHoldsPercent !== null) {
            return false;
        }
    } else {
        if (filters.minDevHoldsPercent !== null && token.dev_holds_percent < filters.minDevHoldsPercent) {
            return false;
        }
        if (filters.maxDevHoldsPercent !== null && token.dev_holds_percent > filters.maxDevHoldsPercent) {
            return false;
        }
    }
    return true;
}

// Используем класс для инкапсуляции состояния на основе рун
class TokenFeedState {
    rawTokens = $state([]);
    filters = $state({ ...DefaultFilters });

    // $derived заменяется на обычный getter внутри класса,
    // Svelte 5 автоматически делает его производным и реактивным
    get filteredTokens() {
        return this.rawTokens.filter(token => passesFilters(token, this.filters));
    }

    addToken(newToken) {
        // Под капотом Svelte 5 отслеживает методы массива
        this.rawTokens.unshift(newToken);
        if (this.rawTokens.length > 500) {
            this.rawTokens.pop();
        }
    }

    updateFilters(newFilters) {
        this.filters = { ...this.filters, ...newFilters };
    }
}

// Экспортируем единственный экземпляр
export const feedState = new TokenFeedState();
