from .domain import DeployedToken, TokenFeedBase


def _migration_share(migrated: int | None, total: int | None) -> str:
    if migrated is None or not total:
        return "⁉️ no history"
    return f"{migrated / total * 100:.1f}%"


def _history_lines(
    tokens: list[DeployedToken] | None, wallet: str
) -> list[str]:
    if not tokens:
        return [f"Tokens not found for dev {wallet}"]
    return [
        f"|- 🪙 {token.token_ticker} ({token.token_name}); "
        f"total fees paid: {token.total_pair_fees_paid}"
        for token in tokens
    ]


def format_token_log(feed: TokenFeedBase) -> str:
    dev_share = _migration_share(
        feed.migrated_tokens_count, feed.all_tokens_count
    )
    lines = [
        "",
        f"🔍 {feed.token_address} ; {feed.token_ticker} ({feed.token_name}) ; "
        f"dev holds: {feed.dev_holds_percent} %",
        f"🛠️ dev: {feed.dev_wallet} ({dev_share} migrated):",
        *_history_lines(feed.last_deployed_tokens, feed.dev_wallet),
    ]
    if feed.funding_wallet is not None:
        funding_share = _migration_share(
            feed.funding_migrated_tokens_count, feed.funding_all_tokens_count
        )
        lines.extend(
            [
                f"💰 funding: {feed.funding_wallet} "
                f"({funding_share} migrated):",
                *_history_lines(
                    feed.funding_deployed_tokens, feed.funding_wallet
                ),
            ]
        )
    return "\n".join(lines) + "\n"
