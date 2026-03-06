from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Dict

from blackjack_ai import rules
from blackjack_ai.cards import InfiniteDeck, Rank
from blackjack_ai.dealer import dealer_outcome_distribution
from blackjack_ai.deck_factory import make_deck
from blackjack_ai.hand import add_card
from blackjack_ai.rules import Rules


@dataclass(frozen=True)
class PlayerState:
    total: int
    soft: bool
    can_double: bool
    can_surrender: bool
    can_split: bool
    pair_rank: int          # 0 means "not a pair"; otherwise 2..11 (Ace=11)
    splits_used: int        # number of splits already performed in this branch


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
    can_split: bool,
    pair_rank: int,
    splits_used: int,
    dealer_upcard: Rank,
    dealer_hits_soft_17: bool,
    allow_double: bool,
    allow_surrender: bool,
    allow_split: bool,
    max_splits: int,
    double_after_split: bool,
    hit_split_aces: bool,
    resplit_aces: bool,
) -> float:
    rules = Rules(
        dealer_hits_soft_17=dealer_hits_soft_17,
        allow_double=allow_double,
        allow_surrender=allow_surrender,
        allow_split=allow_split,
        max_splits=max_splits,
        double_after_split=double_after_split,
        hit_split_aces=hit_split_aces,
        resplit_aces=resplit_aces,
    )
    state = PlayerState(
        total=total,
        soft=soft,
        can_double=can_double,
        can_surrender=can_surrender,
        can_split=can_split,
        pair_rank=pair_rank,
        splits_used=splits_used,
    )

    if state.total > 21:
        return -1.0

    evs = compute_action_evs(state, dealer_upcard, rules)
    return max(evs.values())


def _opt_from_state(state: PlayerState, dealer_upcard: Rank, rules: Rules) -> float:
    return _ev_opt(
        state.total,
        state.soft,
        state.can_double,
        state.can_surrender,
        state.can_split,
        state.pair_rank,
        state.splits_used,
        dealer_upcard,
        rules.dealer_hits_soft_17,
        rules.allow_double,
        rules.allow_surrender,
        rules.allow_split,
        rules.max_splits,
        rules.double_after_split,
        rules.hit_split_aces,
        rules.resplit_aces,
    )


def compute_action_evs(state: PlayerState, dealer_upcard: Rank, rules: Rules) -> Dict[str, float]:
    """
    Returns EVs for all legal actions from this state.
    Actions: stand, hit, double, surrender (optional), split (optional).
    EV units:
      - stand/hit are per 1 unit bet
      - double returns outcomes in +/-2 units (since 2 units wagered)
      - split returns outcomes in +/-2 units (since 2 units wagered after split)
    """
    from blackjack_ai.deck_factory import make_deck
    deck = make_deck(rules)
    evs: Dict[str, float] = {}

    # Stand
    evs["stand"] = ev_stand(state.total, dealer_upcard, rules)

    # Hit: after hit, no surrender/double/split for that hand
    hit_ev = 0.0
    for rank, p in deck.outcomes():
        nt, ns = add_card(state.total, state.soft, rank)
        if nt > 21:
            hit_ev += p * (-1.0)
        else:
            next_state = PlayerState(
                total=nt,
                soft=ns,
                can_double=False,
                can_surrender=False,
                can_split=False,
                pair_rank=0,
                splits_used=state.splits_used,
            )
            hit_ev += p * _opt_from_state(next_state, dealer_upcard, rules)
    evs["hit"] = hit_ev

    # Double: one card then forced stand (2x payoff)
    if rules.allow_double and state.can_double:
        dbl_ev = 0.0
        for rank, p in deck.outcomes():
            nt, ns = add_card(state.total, state.soft, rank)
            if nt > 21:
                dbl_ev += p * (-2.0)
            else:
                dbl_ev += p * (2.0 * ev_stand(nt, dealer_upcard, rules))
        evs["double"] = dbl_ev

    # Surrender: first decision only (EV = -0.5)
    if rules.allow_surrender and state.can_surrender:
        evs["surrender"] = -0.5

    # Split: only if this hand is a pair and splitting is allowed
    if (
        rules.allow_split
        and state.can_split
        and state.pair_rank in (2, 3, 4, 5, 6, 7, 8, 9, 10, 11)
        and state.splits_used < rules.max_splits
    ):
        pr = state.pair_rank

        # Each split hand starts with one card of the pair, then draws one new card.
        # Total EV is sum of both hands (two 1-unit bets), hence range about [-2, +2].
        def ev_one_split_hand() -> float:
            hand_ev = 0.0
            for rank, p in deck.outcomes():
                # Start from single pr card
                t, s = add_card(0, False, pr)
                t, s = add_card(t, s, rank)

                # Split Aces rule: if not allowed to hit split aces, force stand immediately
                if pr == 11 and not rules.hit_split_aces:
                    if t > 21:
                        hand_ev += p * (-1.0)
                    else:
                        hand_ev += p * ev_stand(t, dealer_upcard, rules)
                    continue

                if t > 21:
                    hand_ev += p * (-1.0)
                    continue

                # Determine if this newly formed 2-card hand can be resplit:
                # - only if the drawn card matches the pair card (rank == pr)
                # - only if we still have split budget remaining AFTER this split (splits_used+1 < max_splits)
                # - optionally block resplitting Aces unless rules.resplit_aces is True
                can_resplit = (
                    (rank == pr)
                    and ((state.splits_used + 1) < rules.max_splits)
                    and (pr != 11 or rules.resplit_aces)
                )

                next_state = PlayerState(
                    total=t,
                    soft=s,
                    can_double=rules.double_after_split,
                    can_surrender=False,
                    can_split=can_resplit,
                    pair_rank=(pr if can_resplit else 0),
                    splits_used=state.splits_used + 1,
                )
                hand_ev += p * _opt_from_state(next_state, dealer_upcard, rules)
            return hand_ev

        # Two independent hands with identical distribution in infinite-deck model
        one_hand = ev_one_split_hand()
        evs["split"] = one_hand + one_hand

    return evs


def optimal_ev(state: PlayerState, dealer_upcard: Rank, rules: Rules) -> float:
    return _opt_from_state(state, dealer_upcard, rules)