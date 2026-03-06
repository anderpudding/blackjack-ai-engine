from __future__ import annotations

from functools import lru_cache
from typing import Dict, Tuple

from blackjack_ai.cards import InfiniteDeck, Rank
from blackjack_ai.hand import add_card
from blackjack_ai.rules import Rules

# Distribution keys: 17..21 and "bust"
DealerDist = Dict[str, float]


def _should_dealer_hit(total: int, soft: bool, rules: Rules) -> bool:
    if total < 17:
        return True
    if total > 17:
        return False
    # total == 17
    if soft and rules.dealer_hits_soft_17:
        return True
    return False


@lru_cache(maxsize=None)
def _dealer_play_from_state(total: int, soft: bool, dealer_hits_soft_17: bool) -> Tuple[Tuple[str, float], ...]:
    """
    Returns a normalized distribution of dealer outcomes given current dealer (total, soft).
    Uses infinite-deck draws.
    Cached via primitive args only.
    """
    rules = Rules(dealer_hits_soft_17=dealer_hits_soft_17)
    deck = InfiniteDeck()

    if total > 21:
        return (("bust", 1.0),)

    if not _should_dealer_hit(total, soft, rules):
        if 17 <= total <= 21:
            return ((str(total), 1.0),)
        # Defensive; dealer should not stop outside 17..21 unless bust.
        return (("bust", 1.0),)

    accum: Dict[str, float] = {"bust": 0.0, "17": 0.0, "18": 0.0, "19": 0.0, "20": 0.0, "21": 0.0}
    for rank, p in deck.outcomes():
        nt, ns = add_card(total, soft, rank)
        sub = _dealer_play_from_state(nt, ns, dealer_hits_soft_17)
        for k, prob in sub:
            accum[k] += p * prob

    # Return as tuple for caching friendliness.
    return tuple((k, accum[k]) for k in ["bust", "17", "18", "19", "20", "21"] if accum[k] > 0.0)


@lru_cache(maxsize=None)
def dealer_outcome_distribution(upcard: Rank, dealer_hits_soft_17: bool) -> Dict[str, float]:
    """
    Dealer starts with upcard and draws a hidden card, then plays to completion.
    Returns distribution over: "17","18","19","20","21","bust".
    """
    deck = InfiniteDeck()
    accum: Dict[str, float] = {"bust": 0.0, "17": 0.0, "18": 0.0, "19": 0.0, "20": 0.0, "21": 0.0}

    # Hidden card draw
    for rank, p in deck.outcomes():
        total, soft = add_card(0, False, upcard)
        total, soft = add_card(total, soft, rank)
        dist = _dealer_play_from_state(total, soft, dealer_hits_soft_17)
        for k, prob in dist:
            accum[k] += p * prob

    return accum