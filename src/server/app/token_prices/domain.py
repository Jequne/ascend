from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SolPrice:
    value: float
