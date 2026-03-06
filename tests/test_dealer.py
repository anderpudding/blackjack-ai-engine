from blackjack_ai.cards import parse_rank
from blackjack_ai.dealer import dealer_outcome_distribution


def test_dealer_distribution_sums_to_one():
    up = parse_rank("10")
    dist = dealer_outcome_distribution(up, dealer_hits_soft_17=False)  # S17
    s = sum(dist.values())
    assert abs(s - 1.0) < 1e-9