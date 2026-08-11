export type Terminal = "axiom" | "gmgn";
export type FeesMode = "avg" | "total" | "fixed";
export type SettingsTab = "filters" | "blacklist" | "transfer";

export interface LastDeployedToken {
    blockchain: string;
    total_pair_fees_paid: number;
    ath_mcap_in_usd: number | null;
    dex_paid: boolean;
    pair_address: string;
    token_address: string;
    token_image: string | null;
    is_migrated: boolean;
    website: string | null;
    telegram: string | null;
    discord: string | null;
    twitter: string | null;
    token_name: string;
    token_ticker: string;
    twitter_admin_nickname: string | null;
    twitter_admin_id: string | null;
    dev_wallet: string;
    protocol: string;
    created_at: string;
}

export interface TokenFeedPayload {
    blockchain: "sol" | "bsc";
    indicator: string;
    dev_holds_percent: number | null;
    snipers_hold_percent: number | null;
    pair_address: string;
    token_address: string;
    token_image: string | null;
    is_migrated: boolean;
    website: string | null;
    telegram: string | null;
    discord: string | null;
    twitter: string | null;
    token_name: string;
    token_ticker: string;
    twitter_admin_nickname: string | null;
    twitter_admin_id: string | null;
    dev_wallet: string;
    protocol: string;
    last_deployed_tokens: LastDeployedToken[] | null;
    migrated_tokens_count: number;
    all_tokens_count: number;
}

export interface TokenFeed extends Omit<
    TokenFeedPayload,
    "last_deployed_tokens"
> {
    indicators: string[];
    last_deployed_tokens: LastDeployedToken[];
}

export type WebSocketMessage =
    | { type: "ping"; payload: { timestamp: string } }
    | { type: "sol_price"; payload: number | string }
    | { type: "token_feed"; payload: TokenFeedPayload };

export interface FilterSettings {
    minDevHoldsPercent: number;
    maxDevHoldsPercent: number;
    minMigrationPercent: number;
    feesMode: FeesMode;
    minLastTokenFees: number;
    minLastTokenAthMcap: number;
    lastTokensRequiredCount: number;
    blacklist: string[];
    terminal: Terminal;
    autoOpenInNewTab: boolean;
    aggressiveAutoOpen: boolean;
}

export interface SettingsSections {
    filters: FilterSettings;
}

export interface SettingsEnvelopeV1 {
    schema: "ascend_trenches.settings";
    schemaVersion: 1;
    exportedAt: string;
    settings: SettingsSections;
}

export interface SettingsEnvelopeV2 {
    schema: "ascend_trenches.settings";
    schemaVersion: 2;
    exportedAt: string;
    settings: SettingsSections;
}

export interface BlacklistToken {
    dev_wallet?: string | null;
    token_name?: string | null;
    token_ticker?: string | null;
    twitter_admin_nickname?: string | null;
}

export interface BlacklistMatcher {
    readonly entries: readonly string[];
    matchesText(text: string): boolean;
    matchesToken(token: BlacklistToken): boolean;
}

export interface FilterSnapshot {
    readonly filters: Readonly<FilterSettings>;
    readonly blacklistMatcher: BlacklistMatcher | null;
}

export type FeedRejectionReason =
    "blacklist" | "dev-holds" | "fees" | "migration";

export type FeedDecision =
    | { accepted: true; feed: TokenFeed; reason: null }
    | {
          accepted: false;
          feed: null;
          reason: FeedRejectionReason;
      };
