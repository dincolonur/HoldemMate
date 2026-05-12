"""Deprecated. The Strategy agent now produces the coaching note in the
same JSON response (see `strategy_agent.run_strategy`). This file is kept
only so any older imports don't break; new code should not call into it.
"""

from __future__ import annotations

from typing import Any

from ..game_state import GameState


def run_coach(
    state: GameState,
    math: dict[str, Any],
    opponent: dict[str, Any],
    strategy: dict[str, Any],
) -> str:
    """Compat shim: return the coaching_note from the strategy decision."""
    return str(strategy.get("coaching_note", strategy.get("rationale", "")))
