from __future__ import annotations

import argparse
import sys
from typing import List, Tuple

from blackjack_ai.rules import Rules
from blackjack_ai.strategy import recommend_action


def parse_query(query: str) -> Tuple[List[str], str]:
    s = query.strip()
    parts = s.split("vs")
    if len(parts) != 2:
        raise ValueError("Query must look like: 'A,7 vs 9'")
    left, right = parts[0].strip(), parts[1].strip()
    player_cards = [t.strip() for t in left.split(",") if t.strip()]
    dealer = right.strip()
    return player_cards, dealer


def main() -> int:
    parser = argparse.ArgumentParser(prog="blackjack_ai")
    parser.add_argument("query", help="Example: 'A,7 vs 9'")
    parser.add_argument("--h17", action="store_true", help="Dealer hits soft 17 (H17). Default is S17.")
    parser.add_argument("--surrender", action="store_true", help="Enable late surrender (first decision only).")
    parser.add_argument("--no-double", action="store_true", help="Disable doubling.")

    args = parser.parse_args()

    try:
        player_cards, dealer_up = parse_query(args.query)
        rules = Rules(
            dealer_hits_soft_17=bool(args.h17),
            allow_double=(not args.no_double),
            allow_surrender=bool(args.surrender),
        )
        rec = recommend_action(player_cards, dealer_up, rules)
        print(f"{player_cards} vs {dealer_up} -> {rec.action}")
        for k, v in sorted(rec.evs.items()):
            print(f"  {k:>9}: {v:.6f}")
        return 0
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())