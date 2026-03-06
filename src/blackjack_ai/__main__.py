from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Tuple

from blackjack_ai.rules import Rules
from blackjack_ai.strategy import recommend_action
from blackjack_ai.tablegen import (
    generate_hard_totals,
    generate_pairs,
    generate_soft_totals,
    write_csv,
    write_html,
    write_png,
)


def parse_query(query: str) -> Tuple[List[str], str]:
    s = query.strip()
    parts = s.split("vs")
    if len(parts) != 2:
        raise ValueError("Query must look like: 'A,7 vs 9'")
    left, right = parts[0].strip(), parts[1].strip()
    player_cards = [t.strip() for t in left.split(",") if t.strip()]
    dealer = right.strip()
    return player_cards, dealer


def build_rules(args: argparse.Namespace) -> Rules:
    return Rules(
        dealer_hits_soft_17=bool(getattr(args, "h17", False)),
        allow_double=(not getattr(args, "no_double", False)),
        allow_surrender=bool(getattr(args, "surrender", False)),
        allow_split=(not getattr(args, "no_split", False)),
        max_splits=int(getattr(args, "max_splits", 1)),
        double_after_split=(not getattr(args, "no_das", False)),
        hit_split_aces=bool(getattr(args, "hit_split_aces", False)),
        resplit_aces=bool(getattr(args, "resplit_aces", False)),
    )


def cmd_query(args: argparse.Namespace) -> int:
    player_cards, dealer_up = parse_query(args.query)
    rules = build_rules(args)
    rec = recommend_action(player_cards, dealer_up, rules)
    print(f"{player_cards} vs {dealer_up} -> {rec.action}")
    for k, v in sorted(rec.evs.items()):
        print(f"  {k:>9}: {v:.6f}")
    return 0


def cmd_table(args: argparse.Namespace) -> int:
    rules = build_rules(args)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    hard = generate_hard_totals(rules)
    soft = generate_soft_totals(rules)
    pairs = generate_pairs(rules)

    if args.csv:
        write_csv(hard, out_dir / "hard_totals.csv")
        write_csv(soft, out_dir / "soft_totals.csv")
        write_csv(pairs, out_dir / "pairs.csv")

    if args.html:
        write_html([hard, soft, pairs], out_dir / "strategy.html")

    if args.png:
        write_png(hard, out_dir / "hard_totals.png")
        write_png(soft, out_dir / "soft_totals.png")
        write_png(pairs, out_dir / "pairs.png")

    print(f"Wrote outputs to: {out_dir.resolve()}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(prog="blackjack_ai")
    sub = p.add_subparsers(dest="cmd", required=True)

    # query subcommand
    q = sub.add_parser("query", help="Get best action for a single hand, e.g. '8,8 vs 6'")
    q.add_argument("query", help="Example: 'A,7 vs 9'")
    q.add_argument("--h17", action="store_true")
    q.add_argument("--surrender", action="store_true")
    q.add_argument("--no-double", action="store_true")
    q.add_argument("--no-split", action="store_true")
    q.add_argument("--max-splits", type=int, default=1)
    q.add_argument("--no-das", action="store_true")
    q.add_argument("--hit-split-aces", action="store_true")
    q.add_argument("--resplit-aces", action="store_true")
    q.set_defaults(fn=cmd_query)

    # table subcommand
    t = sub.add_parser("table", help="Generate full basic strategy tables")
    t.add_argument("--out", default="outputs/strategy", help="Output directory")
    t.add_argument("--csv", action="store_true", help="Write CSV tables")
    t.add_argument("--html", action="store_true", help="Write an HTML page with tables")
    t.add_argument("--png", action="store_true", help="Write PNG images (requires matplotlib)")
    t.add_argument("--h17", action="store_true")
    t.add_argument("--surrender", action="store_true")
    t.add_argument("--no-double", action="store_true")
    t.add_argument("--no-split", action="store_true")
    t.add_argument("--max-splits", type=int, default=1)
    t.add_argument("--no-das", action="store_true")
    t.add_argument("--hit-split-aces", action="store_true")
    t.add_argument("--resplit-aces", action="store_true")
    t.set_defaults(fn=cmd_table)

    args = p.parse_args()
    try:
        return int(args.fn(args))
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())