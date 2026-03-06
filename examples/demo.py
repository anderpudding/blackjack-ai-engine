from blackjack_ai.rules import Rules
from blackjack_ai.strategy import recommend_action


def main() -> None:
    rules = Rules(dealer_hits_soft_17=False)  # S17
    scenarios = [
        (["10", "6"], "10"),
        (["10", "2"], "4"),
        (["5", "6"], "6"),
        (["A", "7"], "9"),
    ]

    for player_cards, dealer_up in scenarios:
        rec = recommend_action(player_cards, dealer_up, rules)
        print(f"{player_cards} vs {dealer_up} -> {rec.action} (EVs={rec.evs})")


if __name__ == "__main__":
    main()