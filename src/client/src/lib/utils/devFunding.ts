import type { FilterSettings, TokenFeedPayload } from "$lib/types";
import { passesFundingFeesFilter } from "$lib/utils/fundingFees";

type FundingCandidate = Pick<
    TokenFeedPayload,
    | "blockchain"
    | "funding_wallet"
    | "funding_deployed_tokens"
    | "funding_migrated_tokens_count"
    | "funding_all_tokens_count"
>;

type FundingSettings = Pick<
    FilterSettings,
    | "fundingEnabled"
    | "fundingFeesMode"
    | "minFundingTokenFees"
    | "minFundingMigrationPercent"
>;

/** Decide whether the locally configured Dev Funding strategy accepts a token. */
export function passesDevFundingStrategy(
    candidate: FundingCandidate,
    settings: FundingSettings,
): boolean {
    return (
        settings.fundingEnabled &&
        candidate.blockchain === "sol" &&
        Boolean(candidate.funding_wallet?.trim()) &&
        candidate.funding_all_tokens_count != null &&
        candidate.funding_all_tokens_count > 0 &&
        candidate.funding_migrated_tokens_count != null &&
        candidate.funding_migrated_tokens_count >= 0 &&
        candidate.funding_migrated_tokens_count <=
            candidate.funding_all_tokens_count &&
        (candidate.funding_migrated_tokens_count /
            candidate.funding_all_tokens_count) *
            100 >=
            settings.minFundingMigrationPercent &&
        passesFundingFeesFilter(
            candidate.funding_deployed_tokens,
            settings.fundingFeesMode,
            settings.minFundingTokenFees,
        )
    );
}
