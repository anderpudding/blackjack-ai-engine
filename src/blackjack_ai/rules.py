from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Rules:
    # False => S17, True => H17
    dealer_hits_soft_17: bool = False

    # Double allowed
    allow_double: bool = True

    # Late surrender (first decision only)
    allow_surrender: bool = False

    # Splitting
    allow_split: bool = True
    max_splits: int = 1              # number of split operations allowed
    double_after_split: bool = True  # DAS
    hit_split_aces: bool = False     # False => split Aces get one card then stand
    resplit_aces: bool = False       # allow resplitting A,A when max_splits > 1

    # Deck configuration
    decks: int = 6
    finite_shoe: bool = False