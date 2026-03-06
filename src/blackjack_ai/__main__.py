from __future__ import annotations

import sys
from typing import List

from blackjack_ai.rules import Rules
from blackjack_ai.strategy import recommend_action


def parse_query(args: List[str]) -> tuple[list[str], str]:
    """
    Accept formats:
      python -m blackjack_ai "A,7 vs 9"
      python -m blackjack_ai A,7 vs 9
    """
    if len(args) == 1:
        s = args[0].strip()
        parts = s.split("vs")
        if len(parts) != 2:
            raise ValueError("Query must look like: 'A,7 vs 9'")
        left, right = parts[0].strip(), parts[1].strip()
        player_cards = [t.strip() for t in left.split(",") if t.strip()]
        dealer = right
        return player_cards, dealer

    # Example: A,7 vs 9
    if len(args) == 3 and args[1].lower() == "vs":
        player_cards = [t.strip() for t in args[0].split(",") if t.strip()]
        dealer = args[2].strip()
        return player_cards, dealer

    raise ValueError("Usage: python -m blackjack_ai 'A,7 vs 9'")


def main() -> int:
    try:
        player_cards, dealer_up = parse_query(sys.argv[1:])
        rules = Rules(dealer_hits_soft_17=False, allow_double=True)
        rec = recommend_action(player_cards, dealer_up, rules)
        print(f"{player_cards} vs {dealer_up} -> {rec.action}")
        for k, v in sorted(rec.evs.items()):
            print(f"  {k:>6}: {v:.6f}")
        return 0
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())