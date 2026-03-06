from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Rules:
    # False => S17, True => H17
    dealer_hits_soft_17: bool = False

    # Double allowed (assumed any 2-card hand for v1)
    allow_double: bool = True

    # Late surrender (v1): allowed only as first decision (before hit/double)
    allow_surrender: bool = False