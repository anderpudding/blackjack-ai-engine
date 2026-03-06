from blackjack_ai.rules import Rules
from blackjack_ai.strategy import recommend_action


def test_directional_basic_strategy_checks():
    rules = Rules(dealer_hits_soft_17=False, allow_double=True)  # S17

    # 11 vs 6 should be double in typical basic strategy
    rec = recommend_action(["5", "6"], "6", rules)
    assert rec.action == "double"

    # 12 vs 4 typically stands
    rec = recommend_action(["10", "2"], "4", rules)
    assert rec.action == "stand"