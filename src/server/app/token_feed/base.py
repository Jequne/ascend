from typing import Literal

from .domain import PairEvent, TokenFeedBase


def prepare_base(new_pairs_data: PairEvent) -> TokenFeedBase:
    blockchain: Literal["sol", "bsc"] = "bsc" if "bnb" in new_pairs_data.room else "sol"

    token_feed_base = TokenFeedBase(
        blockchain=blockchain,
        dev_holds_percent=new_pairs_data.content.dev_holds_percent,
        snipers_hold_percent=new_pairs_data.content.snipers_hold_percent,
        pair_address=new_pairs_data.content.pair_address,
        token_address=new_pairs_data.content.token_address,
        token_image=new_pairs_data.content.token_image,
        is_migrated=True if new_pairs_data.content.extra else False,
        website=new_pairs_data.content.website,
        twitter=new_pairs_data.content.twitter,
        telegram=new_pairs_data.content.telegram,
        discord=new_pairs_data.content.discord,
        token_name=new_pairs_data.content.token_name,
        token_ticker=new_pairs_data.content.token_ticker,
        dev_wallet=new_pairs_data.content.deployer_address,
        protocol=new_pairs_data.content.protocol,
        last_deployed_tokens=None,
        migrated_tokens_count=0,
        all_tokens_count=0,
        funding_wallet=None,
        funding_deployed_tokens=None,
    )

    return token_feed_base
