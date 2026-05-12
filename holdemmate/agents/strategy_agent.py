"""Strategy + Coach merged Agent.

This single Claude call now does what the previous Strategy and Coach agents
did separately: picks the action AND writes the plain-language explanation.
Halving the round trips is the biggest single latency win we have.
"""

from __future__ import annotations

from typing import Any

from ..game_state import GameState
from .base import call_claude, parse_json_block

SYSTEM = """You are the Strategy + Coach in a Texas Hold'em decision pipeline.

Given the hand state, the math (equity, pot odds, made-hand class), and the \
opponent read, decide on the best action AND write a short coaching note.

Available actions:
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
  "rationale": "one short paragraph explaining the choice (1-2 sentences)",
  "coaching_note": "friendly 3-5 sentence note for the user explaining WHY \
this action makes sense given equity and pot odds, plus what to watch for \
on the next street. Conversational, like a study-group friend. No bullet lists."
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
        "Decide the best action and write the coaching note."
    )
    raw = call_claude(SYSTEM, user, max_tokens=600, temperature=0.3)
    try:
        decision = parse_json_block(raw)
    except Exception:
        decision = {
            "action": "CHECK" if not math["needs_to_call"] else "FOLD",
            "size_hint": None,
            "confidence": 0.3,
            "rationale": "Fallback (model returned non-JSON): " + raw[:300],
            "coaching_note": (
                "I couldn't parse the model's response cleanly, so I'm "
                "falling back to the safest action."
            ),
        }

    # Defensive normalisation of the action.
    action = str(decision.get("action", "")).upper()
    if action not in {"RAISE", "CALL", "CHECK", "FOLD"}:
        action = "CHECK" if not math["needs_to_call"] else "FOLD"
    if action == "CALL" and not math["needs_to_call"]:
        action = "CHECK"
    if action == "CHECK" and math["needs_to_call"]:
        action = "FOLD"
    decision["action"] = action

    # Make sure coaching_note exists even if the model omitted it.
    decision.setdefault("coaching_note", decision.get("rationale", ""))
    return decision
