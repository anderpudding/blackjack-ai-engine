from blackjack_ai.rules import Rules
from blackjack_ai.strategy import recommend_action
from blackjack_ai.ev_engine import PlayerState, compute_action_evs
from blackjack_ai.rules import Rules
from blackjack_ai.cards import parse_rank


def test_directional_basic_strategy_checks():
    rules = Rules(dealer_hits_soft_17=False, allow_double=True, allow_surrender=False)  # S17

    rec = recommend_action(["5", "6"], "6", rules)
    assert rec.action == "double"

    rec = recommend_action(["10", "2"], "4", rules)
    assert rec.action == "stand"


def test_split_action_available_for_pairs():
    rules = Rules(
        dealer_hits_soft_17=False,
        allow_double=True,
        allow_surrender=False,
        allow_split=True,
        max_splits=1,
        double_after_split=True,
        hit_split_aces=False,
    )
    rec = recommend_action(["8", "8"], "6", rules)
    assert "split" in rec.evs


def test_split_disabled_when_not_pair():
    rules = Rules(allow_split=True)
    rec = recommend_action(["8", "7"], "6", rules)
    assert "split" not in rec.evs

def test_resplit_available_when_under_max_splits():
    rules = Rules(
        allow_split=True,
        max_splits=2,              # allow resplit
        double_after_split=True,
        hit_split_aces=False,
        resplit_aces=False,
    )
    dealer_up = parse_rank("6")

    # Represents a hand that is currently a pair of 8s (post-split), with 1 split already used.
    state = PlayerState(
        total=16,
        soft=False,
        can_double=True,
        can_surrender=False,
        can_split=True,
        pair_rank=8,
        splits_used=1,
    )

    evs = compute_action_evs(state, dealer_up, rules)
    assert "split" in evs