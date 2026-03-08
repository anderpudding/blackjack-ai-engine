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

def format_evs(evs: Dict[str, float]) -> str:
    # Compact, stable ordering for logs/csv
    keys = sorted(evs.keys())
    return ";".join(f"{k}={evs[k]:.6f}" for k in keys)


def ev_columns() -> List[str]:
    # Union of possible actions, used as CSV columns
    return ["hit", "stand", "double", "split", "surrender"]

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


def generate_hard_totals(rules: Rules, explain: bool = False) -> Tuple[Table, List[List[Dict[str, float]]] | None]:
    row_totals = list(range(5, 22))
    row_labels = [str(t) for t in row_totals]
    col_labels = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "A"]

    cells: List[List[str]] = []
    evs_grid: List[List[Dict[str, float]]] = []

    for total in row_totals:
        row: List[str] = []
        ev_row: List[Dict[str, float]] = []
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
            if explain:
                ev_row.append(evs)
        cells.append(row)
        if explain:
            evs_grid.append(ev_row)

    table = Table("Hard Totals", row_labels, col_labels, cells)
    return table, (evs_grid if explain else None)


def generate_soft_totals(rules: Rules, explain: bool = False) -> Tuple[Table, List[List[Dict[str, float]]] | None]:
    # Soft totals A,2 .. A,9 => totals 13..20
    row_totals = list(range(13, 21))
    row_labels = [f"A,{t-11}" for t in row_totals]  # 13->A,2 ... 20->A,9
    col_labels = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "A"]

    cells: List[List[str]] = []
    evs_grid: List[List[Dict[str, float]]] = []

    for total in row_totals:
        row: List[str] = []
        ev_row: List[Dict[str, float]] = []
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
            if explain:
                ev_row.append(evs)
        cells.append(row)
        if explain:
            evs_grid.append(ev_row)

    table = Table("Soft Totals", row_labels, col_labels, cells)
    return table, (evs_grid if explain else None)


def generate_pairs(rules: Rules, explain: bool = False) -> Tuple[Table, List[List[Dict[str, float]]] | None]:
    # Pairs: 2,2 .. A,A
    pair_ranks = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    row_labels = ["2,2", "3,3", "4,4", "5,5", "6,6", "7,7", "8,8", "9,9", "10,10", "A,A"]
    col_labels = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "A"]

    cells: List[List[str]] = []
    evs_grid: List[List[Dict[str, float]]] = []

    for pr in pair_ranks:
        # Pair total in this abstraction
        if pr == 11:
            total, soft = 12, True  # A,A => 12 (soft)
        else:
            total, soft = pr * 2, False

        row: List[str] = []
        ev_row: List[Dict[str, float]] = []
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
            if explain:
                ev_row.append(evs)
        cells.append(row)
        if explain:
            evs_grid.append(ev_row)

    table = Table("Pairs", row_labels, col_labels, cells)
    return table, (evs_grid if explain else None)

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
    import matplotlib.pyplot as plt

    path.parent.mkdir(parents=True, exist_ok=True)

    # Action colors
    color_map = {
        "H": "#f4cccc",  # light red
        "S": "#d9ead3",  # light green
        "D": "#cfe2f3",  # light blue
        "P": "#fff2cc",  # light yellow
        "R": "#ead1dc",  # light purple
    }

    n_rows = len(table.row_labels)
    n_cols = len(table.col_labels)

    fig_width = max(8, n_cols + 2)
    fig_height = max(4, n_rows * 0.45 + 1.5)

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.axis("off")

    # Full table text with header row/column
    cell_text = [[""] + table.col_labels]
    cell_colors = [["#f3f3f3"] * (n_cols + 1)]

    for row_label, row in zip(table.row_labels, table.cells):
        text_row = [row_label]
        color_row = ["#f3f3f3"]

        for cell in row:
            text_row.append(cell)
            color_row.append(color_map.get(cell, "#ffffff"))

        cell_text.append(text_row)
        cell_colors.append(color_row)

    tbl = ax.table(
        cellText=cell_text,
        cellColours=cell_colors,
        loc="center",
        cellLoc="center",
    )

    tbl.auto_set_font_size(False)
    tbl.set_fontsize(11)
    tbl.scale(1.1, 1.4)

    # Bold headers + improve borders
    for (r, c), cell in tbl.get_celld().items():
        cell.set_edgecolor("#444444")
        cell.set_linewidth(0.8)
        if r == 0 or c == 0:
            cell.set_text_props(weight="bold")

    ax.set_title(table.title, fontsize=16, weight="bold", pad=16)

    # Legend
    legend_items = [
        ("H", "Hit", color_map["H"]),
        ("S", "Stand", color_map["S"]),
        ("D", "Double", color_map["D"]),
        ("P", "Split", color_map["P"]),
        ("R", "Surrender", color_map["R"]),
    ]

    color_map = {
        "H": "#e06666",
        "S": "#93c47d",
        "D": "#6fa8dc",
        "P": "#ffd966",
        "R": "#c27ba0",
    }

    legend_text = "   ".join(f"{code}={label}" for code, label, _ in legend_items)
    fig.text(0.5, 0.02, legend_text, ha="center", fontsize=10)

    fig.tight_layout(rect=[0, 0.05, 1, 0.95])
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def write_evs_csv(
    table: Table,
    evs_grid: List[List[Dict[str, float]]],
    path: Path,
) -> None:
    """
    Writes a CSV where each cell includes chosen action + EVs per action.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = ev_columns()

    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        header = ["table", "row", "dealer", "best", "best_code"] + [f"ev_{c}" for c in cols]
        w.writerow(header)

        for r_idx, row_label in enumerate(table.row_labels):
            for c_idx, dealer_label in enumerate(table.col_labels):
                evs = evs_grid[r_idx][c_idx]
                best = best_action(evs)
                row = [
                    table.title,
                    row_label,
                    dealer_label,
                    best,
                    action_code(best),
                ]
                for c in cols:
                    row.append(f"{evs.get(c, float('nan')):.6f}" if c in evs else "")
                w.writerow(row)


def write_flips_csv(
    table_title: str,
    row_labels: List[str],
    col_labels: List[str],
    base_evs: List[List[Dict[str, float]]],
    var_evs: List[List[Dict[str, float]]],
    path: Path,
) -> None:
    """
    Writes rows where best action differs between two rule sets.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = ev_columns()

    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        header = (
            ["table", "row", "dealer", "base_best", "var_best"]
            + [f"base_ev_{c}" for c in cols]
            + [f"var_ev_{c}" for c in cols]
        )
        w.writerow(header)

        for r_idx, row_label in enumerate(row_labels):
            for c_idx, dealer_label in enumerate(col_labels):
                b = base_evs[r_idx][c_idx]
                v = var_evs[r_idx][c_idx]
                b_best = best_action(b)
                v_best = best_action(v)
                if b_best == v_best:
                    continue

                row = [table_title, row_label, dealer_label, b_best, v_best]
                for c in cols:
                    row.append(f"{b.get(c, float('nan')):.6f}" if c in b else "")
                for c in cols:
                    row.append(f"{v.get(c, float('nan')):.6f}" if c in v else "")
                w.writerow(row)


def write_diff_png(
    table_title: str,
    row_labels: List[str],
    col_labels: List[str],
    base_evs: List[List[Dict[str, float]]],
    var_evs: List[List[Dict[str, float]]],
    path: Path,
) -> None:
    import matplotlib.pyplot as plt

    path.parent.mkdir(parents=True, exist_ok=True)

    # Changed cells are colored by the VARIANT action.
    # Unchanged cells are gray.
    color_map = {
        "H": "#f4cccc",  # light red
        "S": "#d9ead3",  # light green
        "D": "#cfe2f3",  # light blue
        "P": "#fff2cc",  # light yellow
        "R": "#ead1dc",  # light purple
    }
    unchanged_color = "#eeeeee"
    header_color = "#f3f3f3"

    n_rows = len(row_labels)
    n_cols = len(col_labels)

    fig_width = max(8, n_cols + 2)
    fig_height = max(4, n_rows * 0.45 + 1.5)

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.axis("off")

    cell_text = [[""] + col_labels]
    cell_colors = [[header_color] * (n_cols + 1)]

    for r_idx, row_label in enumerate(row_labels):
        text_row = [row_label]
        color_row = [header_color]

        for c_idx, dealer_label in enumerate(col_labels):
            b = base_evs[r_idx][c_idx]
            v = var_evs[r_idx][c_idx]

            b_best = best_action(b)
            v_best = best_action(v)

            b_code = action_code(b_best)
            v_code = action_code(v_best)

            if b_best == v_best:
                text_row.append("·")
                color_row.append(unchanged_color)
            else:
                text_row.append(v_code)
                color_row.append(color_map.get(v_code, "#ffffff"))

        cell_text.append(text_row)
        cell_colors.append(color_row)

    tbl = ax.table(
        cellText=cell_text,
        cellColours=cell_colors,
        loc="center",
        cellLoc="center",
    )

    tbl.auto_set_font_size(False)
    tbl.set_fontsize(11)
    tbl.scale(1.1, 1.4)

    for (r, c), cell in tbl.get_celld().items():
        cell.set_edgecolor("#444444")
        cell.set_linewidth(0.8)
        if r == 0 or c == 0:
            cell.set_text_props(weight="bold")
        else:
            if cell.get_text().get_text() != "·":
                cell.set_text_props(weight="bold")

    ax.set_title(table_title, fontsize=16, weight="bold", pad=16)

    legend_text = (
        "· = unchanged    "
        "H = Hit    "
        "S = Stand    "
        "D = Double    "
        "P = Split    "
        "R = Surrender"
    )
    fig.text(0.5, 0.02, legend_text, ha="center", fontsize=10)

    fig.tight_layout(rect=[0, 0.05, 1, 0.95])
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def comparison_label(compare_mode: str) -> str:
    mapping = {
        "h17": "Base vs H17",
        "surrender": "Base vs Late Surrender",
        "h17+surrender": "Base vs H17 + Late Surrender",
    }
    return mapping.get(compare_mode, "Rule Comparison")