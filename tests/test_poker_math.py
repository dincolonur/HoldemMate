"""Smoke tests for the deterministic poker math.

These tests don't hit the LLM — they only exercise treys + Monte Carlo so they
can run in CI without an API key.
"""

from __future__ import annotations

import pytest

from holdemmate.poker_math import hand_class, monte_carlo_equity, pot_odds_pct


def test_aces_dominates_72o_heads_up() -> None:
    """Pocket aces should be ~85% favorite vs 7-2 offsuit pre-flop."""
    result = monte_carlo_equity(
        hole=["As", "Ac"],
        board=[],
        num_opponents=1,
        trials=500,
        seed=1,
    )
    assert 75.0 <= result.equity <= 95.0
    assert result.trials == 500


def test_made_hand_class_on_flop() -> None:
    klass = hand_class(["As", "Ac"], ["Ah", "Kd", "2c"])
    assert "Three of a Kind" in klass or "Trips" in klass or "Set" in klass.lower() \
        or klass == "Three of a Kind"


def test_pot_odds_calc() -> None:
    # Pot 10, to call 5: required equity = 5 / (10 + 10) = 25%
    odds = pot_odds_pct(10.0, 5.0)
    assert odds is not None
    assert abs(odds - 25.0) < 0.01


def test_pot_odds_no_bet() -> None:
    assert pot_odds_pct(10.0, 0.0) is None


def test_invalid_board_length() -> None:
    with pytest.raises(ValueError):
        monte_carlo_equity(["As", "Ac"], ["Ah", "Kd"], num_opponents=1, trials=10)
