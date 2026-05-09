"""Opponent Agent — qualitative read of the villain(s)' likely range."""

from __future__ import annotations

from typing import Any

from ..game_state import GameState
from .base import call_claude, parse_json_block

SYSTEM = """You are the Opponent Modeling Agent in a Texas Hold'em decision pipeline.

Given the hand state, infer what the opponent(s) are likely holding and the main \
threats on the current board. Be concise and concrete.

Respond ONLY with a single JSON object using this schema:
{
  "likely_range": "short description of the opponent's likely hand range",
  "main_threats": ["threat 1", "threat 2", ...],
  "tightness": "tight | balanced | loose",
  "notes": "1-2 sentences of additional reasoning"
}
"""


def run_opponent(state: GameState, math: dict[str, Any]) -> dict[str, Any]:
    user = (
        "HAND STATE\n"
        f"{state.summary()}\n\n"
        "MATH SO FAR\n"
        f"Hero equity vs random ranges: {math['equity_value']:.1f}%\n"
        f"Hero made hand: {math['made_hand']}\n"
        f"Pot odds required: {math['pot_odds_pct']}\n\n"
        "What is each opponent likely holding, and what are the main threats?"
    )
    raw = call_claude(SYSTEM, user, max_tokens=500, temperature=0.5)
    try:
        return parse_json_block(raw)
    except Exception:
        return {
            "likely_range": "unknown (model returned non-JSON)",
            "main_threats": [],
            "tightness": "balanced",
            "notes": raw[:400],
        }
