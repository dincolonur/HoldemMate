"""Strategy Agent — picks RAISE / CALL / CHECK / FOLD."""

from __future__ import annotations

from typing import Any

from ..game_state import GameState
from .base import call_claude, parse_json_block

SYSTEM = """You are the Strategy Agent in a Texas Hold'em decision pipeline.

Given the hand state, the math (equity, pot odds, made-hand class), and the \
opponent read, decide on the best action. Available actions:

- "RAISE"  : bet or raise (specify a sensible size as a multiple of the pot or BB)
- "CALL"   : call the current bet (only if there is a bet to call)
- "CHECK"  : check (only if there is no bet to call)
- "FOLD"   : fold

Rules of thumb:
- If equity clearly exceeds pot odds, CALL or RAISE rather than FOLD.
- If equity is high AND board favors hero's range, lean RAISE for value.
- If equity is borderline and opponents look strong, lean CHECK/FOLD.
- Never CALL when there is nothing to call — use CHECK instead.
- Never CHECK when there is a bet to call — use CALL or FOLD instead.

Respond ONLY with a single JSON object using this schema:
{
  "action": "RAISE" | "CALL" | "CHECK" | "FOLD",
  "size_hint": "e.g. '2.5x pot', '3bb', or null",
  "confidence": 0.0-1.0,
  "rationale": "one short paragraph explaining the choice"
}
"""


def run_strategy(
    state: GameState,
    math: dict[str, Any],
    opponent: dict[str, Any],
) -> dict[str, Any]:
    user = (
        "HAND STATE\n"
        f"{state.summary()}\n\n"
        "MATH\n"
        f"Equity (win+tie/2): {math['equity_value']:.2f}%\n"
        f"Made hand: {math['made_hand']}\n"
        f"Pot odds required: {math['pot_odds_pct']}\n"
        f"Needs to call: {math['needs_to_call']}\n\n"
        "OPPONENT READ\n"
        f"{opponent}\n\n"
        "Recommend the best action."
    )
    raw = call_claude(SYSTEM, user, max_tokens=500, temperature=0.3)
    try:
        decision = parse_json_block(raw)
    except Exception:
        decision = {
            "action": "CHECK" if not math["needs_to_call"] else "FOLD",
            "size_hint": None,
            "confidence": 0.3,
            "rationale": "Fallback (model returned non-JSON): " + raw[:300],
        }

    # Defensive normalisation
    action = str(decision.get("action", "")).upper()
    if action not in {"RAISE", "CALL", "CHECK", "FOLD"}:
        action = "CHECK" if not math["needs_to_call"] else "FOLD"
    if action == "CALL" and not math["needs_to_call"]:
        action = "CHECK"
    if action == "CHECK" and math["needs_to_call"]:
        action = "FOLD"
    decision["action"] = action
    return decision
