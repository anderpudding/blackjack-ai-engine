from blackjack_ai.cards import InfiniteDeck
from blackjack_ai.rules import Rules
from blackjack_ai.shoe import FiniteShoe


def make_deck(rules: Rules):
    if rules.finite_shoe:
        return FiniteShoe.standard(rules.decks)
    return InfiniteDeck()