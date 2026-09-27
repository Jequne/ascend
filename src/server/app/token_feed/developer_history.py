from .domain import HistoryToken


def select_developer_tokens(
    tokens: list[HistoryToken], current_pair_address: str, limit: int = 3
) -> list[HistoryToken]:
    if tokens and tokens[0].pair_address == current_pair_address:
        return tokens[1 : limit + 1]
    return tokens[:limit]
