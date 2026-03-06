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
    max_splits: int = 1              # 1 => split once into 2 hands (no resplitting)
    double_after_split: bool = True  # DAS
    hit_split_aces: bool = False     # False => split Aces get one card then stand

    # Splitting
    allow_split: bool = True
    max_splits: int = 1
    double_after_split: bool = True
    hit_split_aces: bool = False
    resplit_aces: bool = False   # NEW: allow re-splitting A,A when max_splits > 1