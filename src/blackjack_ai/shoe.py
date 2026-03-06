from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


Rank = int


@dataclass
class FiniteShoe:
    """
    Finite deck shoe model.

    Tracks remaining card counts and returns probabilities
    based on composition.
    """

    counts: Dict[Rank, int]

    @classmethod
    def standard(cls, decks: int = 6) -> "FiniteShoe":
        counts = {
            2: 4 * decks,
            3: 4 * decks,
            4: 4 * decks,
            5: 4 * decks,
            6: 4 * decks,
            7: 4 * decks,
            8: 4 * decks,
            9: 4 * decks,
            10: 16 * decks,
            11: 4 * decks,   # Ace
        }
        return cls(counts)

    def total_cards(self) -> int:
        return sum(self.counts.values())

    def outcomes(self) -> List[Tuple[Rank, float]]:
        total = self.total_cards()
        return [(rank, count / total) for rank, count in self.counts.items() if count > 0]

    def draw(self, rank: Rank) -> None:
        self.counts[rank] -= 1

    def copy(self) -> "FiniteShoe":
        return FiniteShoe(self.counts.copy())