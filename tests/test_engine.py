from blackjack_ai.rules import Rules
from blackjack_ai.strategy import recommend_action


def test_directional_basic_strategy_checks():
    rules = Rules(dealer_hits_soft_17=False, allow_double=True, allow_surrender=False)  # S17
    rec = recommend_action(["5", "6"], "6", rules)
    assert rec.action == "double"

    rec = recommend_action(["10", "2"], "4", rules)
    assert rec.action == "stand"


def test_surrender_enabled_adds_action():
    rules = Rules(dealer_hits_soft_17=False, allow_double=True, allow_surrender=True)
    rec = recommend_action(["10", "6"], "A", rules)
    # Not asserting exact best action (depends on model), only that surrender is considered.
    assert "surrender" in rec.evs
    assert rec.evs["surrender"] == -0.5