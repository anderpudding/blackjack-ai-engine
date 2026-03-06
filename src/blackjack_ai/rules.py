from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Rules:
    dealer_hits_soft_17: bool = False  # False => S17, True => H17
    allow_double: bool = True