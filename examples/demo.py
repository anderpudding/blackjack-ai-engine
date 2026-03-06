from blackjack_ai.rules import Rules
from blackjack_ai.strategy import recommend_action


def main() -> None:
    scenarios = [
        (["10", "6"], "10"),
        (["10", "2"], "4"),
        (["5", "6"], "6"),
        (["A", "7"], "9"),
        (["10", "6"], "A"),
    ]

    print("S17, no surrender:")
    rules = Rules(dealer_hits_soft_17=False, allow_surrender=False)
    for player_cards, dealer_up in scenarios:
        rec = recommend_action(player_cards, dealer_up, rules)
        print(f"{player_cards} vs {dealer_up} -> {rec.action} (EVs={rec.evs})")

    print("\nH17, surrender enabled:")
    rules = Rules(dealer_hits_soft_17=True, allow_surrender=True)
    for player_cards, dealer_up in scenarios:
        rec = recommend_action(player_cards, dealer_up, rules)
        print(f"{player_cards} vs {dealer_up} -> {rec.action} (EVs={rec.evs})")


if __name__ == "__main__":
    main()