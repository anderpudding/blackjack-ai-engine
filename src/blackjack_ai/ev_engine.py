from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Dict

from blackjack_ai.cards import InfiniteDeck, Rank
from blackjack_ai.dealer import dealer_outcome_distribution
from blackjack_ai.hand import add_card
from blackjack_ai.rules import Rules


@dataclass(frozen=True)
class PlayerState:
    total: int
    soft: bool
    can_double: bool
    can_surrender: bool


def ev_stand(player_total: int, dealer_upcard: Rank, rules: Rules) -> float:
    dist = dealer_outcome_distribution(dealer_upcard, rules.dealer_hits_soft_17)
    ev = 0.0
    for outcome, p in dist.items():
        if outcome == "bust":
            ev += 1.0 * p
            continue
        dealer_total = int(outcome)
        if dealer_total < player_total:
            ev += 1.0 * p
        elif dealer_total > player_total:
            ev += -1.0 * p
        else:
            ev += 0.0
    return ev


@lru_cache(maxsize=None)
def _ev_opt(
    total: int,
    soft: bool,
    can_double: bool,
    can_surrender: bool,
    dealer_upcard: Rank,
    dealer_hits_soft_17: bool,
    allow_double: bool,
    allow_surrender: bool,
) -> float:
    rules = Rules(
        dealer_hits_soft_17=dealer_hits_soft_17,
        allow_double=allow_double,
        allow_surrender=allow_surrender,
    )
    state = PlayerState(
        total=total,
        soft=soft,
        can_double=can_double,
        can_surrender=can_surrender,
    )

    if state.total > 21:
        return -1.0

    evs = compute_action_evs(state, dealer_upcard, rules)
    return max(evs.values())


def compute_action_evs(state: PlayerState, dealer_upcard: Rank, rules: Rules) -> Dict[str, float]:
    """
    Returns EVs for all legal actions from this state.
    v1 actions: stand, hit, double, surrender (optional)
    """
    deck = InfiniteDeck()
    evs: Dict[str, float] = {}

    # Stand
    evs["stand"] = ev_stand(state.total, dealer_upcard, rules)

    # Hit (after hitting, surrender/double are no longer allowed)
    hit_ev = 0.0
    for rank, p in deck.outcomes():
        nt, ns = add_card(state.total, state.soft, rank)
        if nt > 21:
            hit_ev += p * (-1.0)
        else:
            hit_ev += p * _ev_opt(
                nt,
                ns,
                False,   # can_double
                False,   # can_surrender
                dealer_upcard,
                rules.dealer_hits_soft_17,
                rules.allow_double,
                rules.allow_surrender,
            )
    evs["hit"] = hit_ev

    # Double (one card then stand; 2x payoff)
    if rules.allow_double and state.can_double:
        dbl_ev = 0.0
        for rank, p in deck.outcomes():
            nt, ns = add_card(state.total, state.soft, rank)
            if nt > 21:
                dbl_ev += p * (-2.0)
            else:
                dbl_ev += p * (2.0 * ev_stand(nt, dealer_upcard, rules))
        evs["double"] = dbl_ev

    # Surrender (late surrender, first decision only; EV = -0.5)
    if rules.allow_surrender and state.can_surrender:
        evs["surrender"] = -0.5

    return evs


def optimal_ev(state: PlayerState, dealer_upcard: Rank, rules: Rules) -> float:
    return _ev_opt(
        state.total,
        state.soft,
        state.can_double,
        state.can_surrender,
        dealer_upcard,
        rules.dealer_hits_soft_17,
        rules.allow_double,
        rules.allow_surrender,
    )