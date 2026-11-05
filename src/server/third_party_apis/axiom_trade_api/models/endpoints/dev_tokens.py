"""Object-shaped response from the current /dev-tokens endpoint."""

from datetime import datetime

from pydantic import BaseModel, Field


class DevTokenCounts(BaseModel):
    total_count: int = Field(alias="totalCount")
    migrated_count: int = Field(alias="migratedCount")


class DevTokenMetadata(BaseModel):
    token_address: str = Field(alias="tokenAddress")
    best_pair_address: str | None = Field(
        default=None, alias="bestPairAddress"
    )
    token_ticker: str | None = Field(default=None, alias="tokenTicker")
    token_name: str | None = Field(default=None, alias="tokenName")
    token_image: str | None = Field(default=None, alias="tokenImage")
    token_created_at: datetime = Field(alias="tokenCreatedAt")
    dex_paid: bool = Field(default=False, alias="dexPaid")
    twitter: str | None = None
    website: str | None = None
    telegram: str | None = None
    discord: str | None = None


class DevTokenPair(BaseModel):
    pair_address: str = Field(alias="pairAddress")
    display_protocol: str = Field(alias="displayProtocol")


class DevTokenEntry(BaseModel):
    token: DevTokenMetadata
    best_pair: DevTokenPair | None = Field(default=None, alias="bestPair")
    is_migrated: bool = Field(alias="isMigrated")
    all_time_high_marketcap_usd: float | None = Field(
        default=None, alias="allTimeHighMarketcapUsd"
    )
    total_pair_fees_paid: float | None = Field(
        default=None, alias="totalPairFeesPaid"
    )


class WalletFunding(BaseModel):
    wallet_address: str = Field(alias="walletAddress")
    funding_wallet_address: str = Field(alias="fundingWalletAddress")


class DevTokensResponse(BaseModel):
    counts: DevTokenCounts
    tokens: list[DevTokenEntry]
    wallet_funding: WalletFunding | None = Field(
        default=None, alias="walletFunding"
    )
