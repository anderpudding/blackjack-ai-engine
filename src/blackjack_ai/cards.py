from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

# Internal rank encoding:
# 2..10 as integers, Ace as 11.
Rank = int

RANK_STR_TO_VALUE: Dict[str, Rank] = {
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "10": 10,
    "J": 10,
    "Q": 10,
    "K": 10,
    "A": 11,
}

VALUE_TO_DISPLAY: Dict[Rank, str] = {
    2: "2",
    3: "3",
    4: "4",
    5: "5",
    6: "6",
    7: "7",
    8: "8",
    9: "9",
    10: "10",
    11: "A",
}


def parse_rank(token: str) -> Rank:
    t = token.strip().upper()
    if t not in RANK_STR_TO_VALUE:
        raise ValueError(f"Invalid card token: {token!r}")
    return RANK_STR_TO_VALUE[t]


def parse_cards(tokens: Iterable[str]) -> List[Rank]:
    return [parse_rank(t) for t in tokens]


@dataclass(frozen=True)
class InfiniteDeck:
    """
    Infinite deck model:
      P(A) = 1/13
      P(2..9) = 1/13 each
      P(10) = 4/13 (10/J/Q/K)
    """

    def outcomes(self) -> List[Tuple[Rank, float]]:
        return [
            (2, 1 / 13),
            (3, 1 / 13),
            (4, 1 / 13),
            (5, 1 / 13),
            (6, 1 / 13),
            (7, 1 / 13),
            (8, 1 / 13),
            (9, 1 / 13),
            (10, 4 / 13),
            (11, 1 / 13),
        ]