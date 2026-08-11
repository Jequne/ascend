import type { LastDeployedToken, TokenFeed } from "$lib/types";

export function createLastDeployedToken(
    overrides: Partial<LastDeployedToken> = {},
): LastDeployedToken {
    return {
        blockchain: "sol",
        total_pair_fees_paid: 1.5,
        ath_mcap_in_usd: 125_000,
        dex_paid: true,
        pair_address: "last-pair",
        token_address: "last-token",
        token_image: null,
        is_migrated: true,
        website: "https://example.com/last",
        telegram: "https://t.me/example",
        discord: "https://discord.gg/example",
        twitter: "https://x.com/example",
        token_name: "Last Token",
        token_ticker: "LAST",
        twitter_admin_nickname: "admin",
        twitter_admin_id: "1",
        dev_wallet: "last-wallet",
        protocol: "pump",
        created_at: "2026-08-10T12:00:00.000Z",
        ...overrides,
    };
}

export function createTokenFeed(overrides: Partial<TokenFeed> = {}): TokenFeed {
    return {
        clientKey: "pair:0",
        blockchain: "sol",
        indicator: "Dev Migrations",
        indicators: ["Dev Migrations"],
        dev_holds_percent: 4.2,
        snipers_hold_percent: null,
        pair_address: "pair",
        token_address: "token",
        token_image: null,
        is_migrated: true,
        website: "https://example.com",
        telegram: "https://t.me/example",
        discord: "https://discord.gg/example",
        twitter: "https://x.com/example",
        token_name: "Example Token",
        token_ticker: "EXM",
        twitter_admin_nickname: "admin",
        twitter_admin_id: "1",
        dev_wallet: "dev-wallet",
        protocol: "pump",
        last_deployed_tokens: [],
        migrated_tokens_count: 4,
        all_tokens_count: 10,
        ...overrides,
    };
}
