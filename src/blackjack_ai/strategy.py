from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from blackjack_ai.cards import Rank, parse_cards, parse_rank
from blackjack_ai.ev_engine import PlayerState, compute_action_evs
from blackjack_ai.hand import hand_from_cards
from blackjack_ai.rules import Rules


@dataclass(frozen=True)
class Recommendation:
    action: str
    evs: Dict[str, float]


def recommend_action(player_cards: List[str], dealer_upcard: str, rules: Rules) -> Recommendation:
    player_ranks: List[Rank] = parse_cards(player_cards)
    dealer_rank: Rank = parse_rank(dealer_upcard)

    hand = hand_from_cards(player_ranks)
    state = PlayerState(total=hand.total, soft=hand.soft, can_double=True)

    evs = compute_action_evs(state, dealer_rank, rules)
    best_action = max(evs, key=lambda a: evs[a])
    return Recommendation(action=best_action, evs=evs)