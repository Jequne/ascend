from pydantic import BaseModel, Field, ConfigDict, model_validator, model_serializer
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import time


class DevWalletFunding(BaseModel):
    amount_sol: float = Field(..., alias="amountSol")
    funded_at: datetime = Field(..., alias="fundedAt")
    funding_wallet_address: str = Field(..., alias="fundingWalletAddress")
    signature: str 
    wallet_address: str = Field(..., alias="walletAddress")


class Extra(BaseModel):
    migrated_from: str = Field(..., alias="migratedFrom")


class ProtocolDetails(BaseModel):
    # associated_bonding_curve: str = Field(..., alias="associatedBondingCurve")
    cashback: bool
    creator: str
    is_mayhem: bool = Field(..., alias="isMayhem")
    is_offchain: bool = Field(..., alias="isOffchain")
    token_program: str = Field(..., alias="tokenProgram")


class PairInfoResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    created_at: datetime = Field(..., alias="createdAt")
    deployer_address: str = Field(..., alias="deployerAddress")
    dev_wallet_funding: DevWalletFunding = Field(..., alias="devWalletFunding")
    dex_paid: bool = Field(..., alias="dexPaid")
    discord: Optional[str]
    display_protocol: str = Field(..., alias="displayProtocol")
    extra: Optional[Extra]
    open_trading: datetime = Field(..., alias="openTrading")
    pair_address: str = Field(..., alias="pairAddress")
    protocol: str
    protocol_details: ProtocolDetails = Field(..., alias="protocolDetails")
    supply: float
    telegram: Optional[str]
    token_address: str = Field(..., alias="tokenAddress")
    token_image: str = Field(..., alias="tokenImage")
    token_name: str = Field(..., alias="tokenName")
    token_ticker: str = Field(..., alias="tokenTicker")
    token_uri: str = Field(..., alias="tokenUri")
    top10_holders: float = Field(..., alias="top10Holders")
    twitter: Optional[str]
    updated_at: datetime = Field(..., alias="updatedAt")
    user_count: int = Field(..., alias="userCount")
    website: Optional[str]