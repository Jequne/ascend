from .contracts import PriceCallback, PriceSource


class PriceService:
    def __init__(self, source: PriceSource, callback: PriceCallback):
        self._source = source
        self._callback = callback

    def start(self) -> None:
        self._source.subscribe(self._callback)

    def stop(self) -> None:
        self._source.unsubscribe(self._callback)
