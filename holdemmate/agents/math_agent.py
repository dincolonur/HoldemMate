"""Math Agent — turns a GameState into hard numbers (equity, pot odds, hand class).

This agent is deterministic and does NOT call the LLM. It produces the factual
inputs that the downstream LLM agents reason about.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from ..config import get_settings
from ..game_state import GameState
from ..poker_math import EquityResult, hand_class, monte_carlo_equity, pot_odds_pct


def run_math(state: GameState) -> dict[str, Any]:
    settings = get_settings()
    equity: EquityResult = monte_carlo_equity(
        hole=state.hole_cards,
        board=state.board,
        num_opponents=state.num_opponents,
        trials=settings.mc_trials,
    )
    pot_odds = pot_odds_pct(state.pot, state.to_call)
    made_hand = hand_class(state.hole_cards, state.board)

    return {
        "equity": asdict(equity),
        "equity_value": equity.equity,
        "pot_odds_pct": pot_odds,
        "made_hand": made_hand,
        "needs_to_call": state.to_call > 0,
    }
