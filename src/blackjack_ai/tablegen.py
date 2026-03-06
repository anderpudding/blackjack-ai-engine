from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from blackjack_ai.cards import parse_rank
from blackjack_ai.ev_engine import PlayerState, compute_action_evs
from blackjack_ai.rules import Rules


DEALER_UPCARDS: List[int] = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]  # 11 = Ace


# Deterministic tie-breaker if EVs are equal (rare but possible due to floats)
ACTION_PREFERENCE: List[str] = ["split", "double", "stand", "hit", "surrender"]


def best_action(evs: Dict[str, float]) -> str:
    best = max(evs.values())
    tied = [a for a, v in evs.items() if abs(v - best) < 1e-12]
    tied.sort(key=lambda a: ACTION_PREFERENCE.index(a) if a in ACTION_PREFERENCE else 999)
    return tied[0]


def action_code(action: str) -> str:
    # Common chart codes
    if action == "hit":
        return "H"
    if action == "stand":
        return "S"
    if action == "double":
        return "D"
    if action == "split":
        return "P"
    if action == "surrender":
        return "R"  # surrender
    return action[:1].upper()


@dataclass(frozen=True)
class Table:
    title: str
    row_labels: List[str]
    col_labels: List[str]
    cells: List[List[str]]  # rows x cols


def _dealer_rank_from_int(v: int) -> int:
    # parse_rank expects strings; dealer upcards are 2..11 (A)
    return v


def _evs_for_state(state: PlayerState, dealer_up_int: int, rules: Rules) -> Dict[str, float]:
    dealer_rank = _dealer_rank_from_int(dealer_up_int)
    return compute_action_evs(state, dealer_rank, rules)


def generate_hard_totals(rules: Rules) -> Table:
    # Typical chart shows hard totals 5..21 (sometimes 8..17 emphasized)
    row_totals = list(range(5, 22))
    row_labels = [str(t) for t in row_totals]
    col_labels = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "A"]

    cells: List[List[str]] = []
    for total in row_totals:
        row: List[str] = []
        for up in DEALER_UPCARDS:
            state = PlayerState(
                total=total,
                soft=False,
                can_double=True,
                can_surrender=True,
                can_split=False,
                pair_rank=0,
                splits_used=0,
            )
            evs = _evs_for_state(state, up, rules)
            row.append(action_code(best_action(evs)))
        cells.append(row)

    return Table("Hard Totals", row_labels, col_labels, cells)


def generate_soft_totals(rules: Rules) -> Table:
    # Soft totals A,2 .. A,9 => totals 13..20
    row_totals = list(range(13, 21))
    row_labels = [f"A,{t-11}" for t in row_totals]  # 13->A,2 ... 20->A,9
    col_labels = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "A"]

    cells: List[List[str]] = []
    for total in row_totals:
        row: List[str] = []
        for up in DEALER_UPCARDS:
            state = PlayerState(
                total=total,
                soft=True,
                can_double=True,
                can_surrender=True,
                can_split=False,
                pair_rank=0,
                splits_used=0,
            )
            evs = _evs_for_state(state, up, rules)
            row.append(action_code(best_action(evs)))
        cells.append(row)

    return Table("Soft Totals", row_labels, col_labels, cells)


def generate_pairs(rules: Rules) -> Table:
    # Pairs: 2,2 .. A,A
    pair_ranks = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    row_labels = ["2,2", "3,3", "4,4", "5,5", "6,6", "7,7", "8,8", "9,9", "10,10", "A,A"]
    col_labels = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "A"]

    cells: List[List[str]] = []
    for pr in pair_ranks:
        # total for a pair is deterministic in this abstraction
        # Ace pair: A,A => total 12 soft (Ace=11 + Ace=1)
        if pr == 11:
            total, soft = 12, True
        else:
            total, soft = pr * 2, False

        row: List[str] = []
        for up in DEALER_UPCARDS:
            state = PlayerState(
                total=total,
                soft=soft,
                can_double=True,
                can_surrender=True,
                can_split=True,
                pair_rank=pr,
                splits_used=0,
            )
            evs = _evs_for_state(state, up, rules)
            row.append(action_code(best_action(evs)))
        cells.append(row)

    return Table("Pairs", row_labels, col_labels, cells)


def write_csv(table: Table, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([table.title] + table.col_labels)
        for label, row in zip(table.row_labels, table.cells):
            w.writerow([label] + row)


def write_html(tables: List[Table], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    def render_table(t: Table) -> str:
        ths = "".join(f"<th>{c}</th>" for c in ([""] + t.col_labels))
        rows = []
        for label, row in zip(t.row_labels, t.cells):
            tds = "".join(f"<td>{cell}</td>" for cell in row)
            rows.append(f"<tr><th>{label}</th>{tds}</tr>")
        body = "\n".join(rows)
        return f"""
        <h2>{t.title}</h2>
        <table>
          <thead><tr>{ths}</tr></thead>
          <tbody>
            {body}
          </tbody>
        </table>
        """

    html_tables = "\n".join(render_table(t) for t in tables)

    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Blackjack Strategy Tables</title>
  <style>
    body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; padding: 16px; }}
    table {{ border-collapse: collapse; margin: 12px 0 24px 0; }}
    th, td {{ border: 1px solid #999; padding: 6px 10px; text-align: center; }}
    thead th {{ position: sticky; top: 0; background: #f5f5f5; }}
  </style>
</head>
<body>
  <h1>Blackjack Strategy Tables</h1>
  <p>Codes: H=Hit, S=Stand, D=Double, P=Split, R=Surrender.</p>
  {html_tables}
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def write_png(table: Table, path: Path) -> None:
    # Optional dependency at runtime; only used if you call this function.
    import matplotlib.pyplot as plt

    path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots()
    ax.axis("off")

    # Build cell text with header row/col
    cell_text = [[""] + table.col_labels]
    for label, row in zip(table.row_labels, table.cells):
        cell_text.append([label] + row)

    ax.table(cellText=cell_text, loc="center")
    ax.set_title(table.title)

    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)