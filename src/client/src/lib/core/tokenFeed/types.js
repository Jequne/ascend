/**
 * @typedef {Object} DeployedToken
 * @property {string} blockchain
 * @property {number} total_pair_fees_paid
 * @property {number|null} ath_mcap_in_usd
 * @property {boolean} dex_paid
 * @property {string} pair_address
 * @property {string} token_address
 * @property {string|null} token_image
 * @property {boolean} is_migrated
 * @property {string|null} website
 * @property {string|null} telegram
 * @property {string|null} discord
 * @property {string|null} twitter
 * @property {string} token_name
 * @property {string} token_ticker
 * @property {string|null} twitter_admin_nickname
 * @property {string|null} twitter_admin_id
 * @property {string} dev_wallet
 * @property {string} protocol
 * @property {string} created_at - ISO datetime string
 */

/**
 * @typedef {Object} TokenFeedBase
 * @property {'sol'|'bsc'} blockchain
 * @property {'Dev Migrations'} indicator
 * @property {number|null} dev_holds_percent
 * @property {number|null} snipers_hold_percent
 * @property {string} pair_address
 * @property {string} token_address
 * @property {string|null} token_image
 * @property {boolean} is_migrated
 * @property {string|null} website
 * @property {string|null} telegram
 * @property {string|null} discord
 * @property {string|null} twitter
 * @property {string} token_name
 * @property {string} token_ticker
 * @property {string|null} twitter_admin_nickname
 * @property {string|null} twitter_admin_id
 * @property {string} dev_wallet
 * @property {string} protocol
 * @property {DeployedToken[]|null} last_deployed_tokens
 * @property {number} migrated_tokens_count
 * @property {number} all_tokens_count
 */

/**
 * Настройки фильтрации пользователя
 * @typedef {Object} TokenFilterSettings
 * @property {number|null} minDevHoldsPercent - Минимальный процент токенов у разработчика
 * @property {number|null} maxDevHoldsPercent - Максимальный процент токенов у разработчика
 */

export const DefaultFilters = {
    minDevHoldsPercent: null,
    maxDevHoldsPercent: null
};
