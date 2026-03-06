from blackjack_ai.hand import hand_from_cards
from blackjack_ai.cards import parse_cards


def test_hand_totals_simple():
    h = hand_from_cards(parse_cards(["10", "6"]))
    assert h.total == 16
    assert h.soft is False


def test_hand_soft_ace():
    h = hand_from_cards(parse_cards(["A", "7"]))
    assert h.total == 18
    assert h.soft is True


def test_hand_ace_adjustment():
    h = hand_from_cards(parse_cards(["A", "9", "A"]))
    # A(11)+9=20 soft, then +A => becomes 21 (Ace as 1)
    assert h.total == 21