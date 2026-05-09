"""Coach Agent — explains the recommendation in plain language."""

from __future__ import annotations

from typing import Any

from ..game_state import GameState
from .base import call_claude

SYSTEM = """You are the Poker Coach in a Texas Hold'em decision pipeline.

Given the hand state, the math, the opponent read, and the strategy decision, \
write a short, friendly explanation (3-5 sentences) for the user.

Cover:
- WHY the recommended action makes sense given equity and pot odds.
- What you would watch for on the next street.
- Keep the tone calm and didactic, like a study-group friend.

Plain text only. No JSON, no bullet lists unless they truly help.
"""


def run_coach(
    state: GameState,
    math: dict[str, Any],
    opponent: dict[str, Any],
    strategy: dict[str, Any],
) -> str:
    user = (
        "HAND STATE\n"
        f"{state.summary()}\n\n"
        "MATH\n"
        f"Equity: {math['equity_value']:.2f}%, "
        f"made hand: {math['made_hand']}, "
        f"pot odds: {math['pot_odds_pct']}\n\n"
        "OPPONENT READ\n"
        f"{opponent}\n\n"
        "STRATEGY DECISION\n"
        f"{strategy}\n\n"
        "Write the coaching note now."
    )
    return call_claude(SYSTEM, user, max_tokens=500, temperature=0.6)
