from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Tuple

from blackjack_ai.cards import InfiniteDeck, VALUE_TO_DISPLAY
from blackjack_ai.rules import Rules
from blackjack_ai.strategy import recommend_action


@dataclass(frozen=True)
class SimResult:
    trials: int
    action_counts: dict


def random_rank(rng: random.Random) -> int:
    # sample from infinite-deck distribution
    x = rng.random()
    # cumulative over [(2..9)=1/13 each, 10=4/13, A=1/13]
    probs = [(2, 1/13), (3, 1/13), (4, 1/13), (5, 1/13), (6, 1/13), (7, 1/13), (8, 1/13), (9, 1/13), (10, 4/13), (11, 1/13)]
    c = 0.0
    for r, p in probs:
        c += p
        if x <= c:
            return r
    return 11


def run_quick_sim(trials: int = 1000, seed: int = 0) -> SimResult:
    rng = random.Random(seed)
    rules = Rules(dealer_hits_soft_17=False, allow_double=True)
    counts = {"stand": 0, "hit": 0, "double": 0}

    for _ in range(trials):
        player = [random_rank(rng), random_rank(rng)]
        dealer_up = random_rank(rng)

        player_str = [VALUE_TO_DISPLAY[r] for r in player]
        dealer_str = VALUE_TO_DISPLAY[dealer_up]
        rec = recommend_action(player_str, dealer_str, rules)
        counts[rec.action] += 1

    return SimResult(trials=trials, action_counts=counts)