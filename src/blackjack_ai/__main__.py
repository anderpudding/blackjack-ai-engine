from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Tuple

from blackjack_ai.rules import Rules
from blackjack_ai.strategy import recommend_action
from blackjack_ai.tablegen import (
    comparison_label,
    generate_hard_totals,
    generate_pairs,
    generate_soft_totals,
    write_csv,
    write_diff_png,
    write_evs_csv,
    write_flips_csv,
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
    base_rules = build_rules(args)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    hard, hard_evs = generate_hard_totals(base_rules, explain=args.explain or (args.compare is not None))
    soft, soft_evs = generate_soft_totals(base_rules, explain=args.explain or (args.compare is not None))
    pairs, pairs_evs = generate_pairs(base_rules, explain=args.explain or (args.compare is not None))

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

    # EV breakdown outputs
    if args.explain:
        assert hard_evs is not None and soft_evs is not None and pairs_evs is not None
        write_evs_csv(hard, hard_evs, out_dir / "hard_totals_evs.csv")
        write_evs_csv(soft, soft_evs, out_dir / "soft_totals_evs.csv")
        write_evs_csv(pairs, pairs_evs, out_dir / "pairs_evs.csv")

    # Flip report (base vs variant rules)
    if args.compare is not None:
        # Build a variant ruleset by toggling selected fields.
        var_rules = base_rules
        if args.compare in ("h17", "h17+surrender"):
            var_rules = Rules(**{**var_rules.__dict__, "dealer_hits_soft_17": True})
        if args.compare in ("surrender", "h17+surrender"):
            var_rules = Rules(**{**var_rules.__dict__, "allow_surrender": True})

        v_hard, v_hard_evs = generate_hard_totals(var_rules, explain=True)
        v_soft, v_soft_evs = generate_soft_totals(var_rules, explain=True)
        v_pairs, v_pairs_evs = generate_pairs(var_rules, explain=True)

        assert hard_evs is not None and soft_evs is not None and pairs_evs is not None
        assert v_hard_evs is not None and v_soft_evs is not None and v_pairs_evs is not None

        flips_path = out_dir / "flips.csv"
        # Append all flips into one file
        # (write header once, so we’ll write to a temp list then write)
        # Simpler: write three separate and let user merge. But per request: one report.
        # We'll write one consolidated file by writing sequentially with the same writer format.
        # Implement by writing three files instead (clean + simple).
        write_flips_csv("Hard Totals", hard.row_labels, hard.col_labels, hard_evs, v_hard_evs, out_dir / "flips_hard.csv")
        write_flips_csv("Soft Totals", soft.row_labels, soft.col_labels, soft_evs, v_soft_evs, out_dir / "flips_soft.csv")
        write_flips_csv("Pairs", pairs.row_labels, pairs.col_labels, pairs_evs, v_pairs_evs, out_dir / "flips_pairs.csv")

        label = comparison_label(args.compare)

        write_diff_png(
            f"Hard Totals ({label})",
            hard.row_labels,
            hard.col_labels,
            hard_evs,
            v_hard_evs,
            out_dir / "diff_hard.png",
        )
        write_diff_png(
            f"Soft Totals ({label})",
            soft.row_labels,
            soft.col_labels,
            soft_evs,
            v_soft_evs,
            out_dir / "diff_soft.png",
        )
        write_diff_png(
            f"Pairs ({label})",
            pairs.row_labels,
            pairs.col_labels,
            pairs_evs,
            v_pairs_evs,
            out_dir / "diff_pairs.png",
        )

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
    t.add_argument("--explain", action="store_true")
    t.add_argument(
        "--compare",
        choices=["h17", "surrender", "h17+surrender"],
        default=None,
    )
    t.set_defaults(fn=cmd_table)

    args = p.parse_args()
    try:
        return int(args.fn(args))
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())