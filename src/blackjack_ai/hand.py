from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

from blackjack_ai.cards import Rank


@dataclass(frozen=True)
class HandState:
    total: int
    soft: bool  # True if an Ace is counted as 11 in the total

    def is_bust(self) -> bool:
        return self.total > 21


def add_card(total: int, soft: bool, rank: Rank) -> Tuple[int, bool]:
    """
    Update (total, soft) after drawing 'rank', applying Ace logic.
    - rank 11 means Ace.
    """
    if rank == 11:
        # Prefer counting Ace as 11 if it doesn't bust.
        if total + 11 <= 21:
            total += 11
            soft = True
        else:
            total += 1
    else:
        total += rank

    # If bust but soft, convert one Ace from 11 to 1.
    if total > 21 and soft:
        total -= 10
        soft = False

    return total, soft


def hand_from_cards(ranks: Iterable[Rank]) -> HandState:
    total = 0
    soft = False
    for r in ranks:
        total, soft = add_card(total, soft, r)
    return HandState(total=total, soft=soft)