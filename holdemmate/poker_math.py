"""Hand evaluation + Monte Carlo equity simulation using `treys`."""

from __future__ import annotations

import random
from dataclasses import dataclass

from treys import Card, Deck, Evaluator

_EVAL = Evaluator()


@dataclass
class EquityResult:
    win_pct: float
    tie_pct: float
    loss_pct: float
    trials: int

    @property
    def equity(self) -> float:
        """Equity = win + tie/2."""
        return self.win_pct + self.tie_pct / 2.0


def _to_treys(cards: list[str]) -> list[int]:
    return [Card.new(c) for c in cards]


def monte_carlo_equity(
    hole: list[str],
    board: list[str],
    num_opponents: int = 1,
    trials: int = 2000,
    seed: int | None = None,
) -> EquityResult:
    """Estimate the hero's equity vs random opponent ranges.

    Args:
        hole: hero's two hole cards as treys strings (e.g. ['Ad', 'Ks']).
        board: 0, 3, 4, or 5 community cards.
        num_opponents: villains drawn random hole cards each trial.
        trials: number of Monte Carlo iterations.
        seed: optional RNG seed for reproducibility.
    """
    if len(hole) != 2:
        raise ValueError("Hero must have exactly 2 hole cards")
    if len(board) not in (0, 3, 4, 5):
        raise ValueError("Board must have 0, 3, 4, or 5 cards")
    if num_opponents < 1:
        raise ValueError("Need at least 1 opponent")

    rng = random.Random(seed)

    hero = _to_treys(hole)
    board_t = _to_treys(board)
    known = set(hole) | set(board)

    wins = ties = losses = 0

    for _ in range(trials):
        deck = Deck()
        # Strip already-known cards out of the deck.
        deck.cards = [c for c in deck.cards if Card.int_to_str(c) not in known]
        rng.shuffle(deck.cards)

        # Deal opponents.
        villains: list[list[int]] = []
        for _v in range(num_opponents):
            villains.append([deck.cards.pop(), deck.cards.pop()])

        # Complete the board.
        full_board = list(board_t)
        while len(full_board) < 5:
            full_board.append(deck.cards.pop())

        hero_score = _EVAL.evaluate(full_board, hero)
        villain_scores = [_EVAL.evaluate(full_board, v) for v in villains]
        best_villain = min(villain_scores)  # lower = better in treys

        if hero_score < best_villain:
            wins += 1
        elif hero_score == best_villain:
            ties += 1
        else:
            losses += 1

    total = float(trials)
    return EquityResult(
        win_pct=wins / total * 100.0,
        tie_pct=ties / total * 100.0,
        loss_pct=losses / total * 100.0,
        trials=trials,
    )


def hand_class(hole: list[str], board: list[str]) -> str:
    """Best-made-hand class for the hero given current board."""
    if not board:
        return "Pre-flop hole cards (no board yet)"
    hero = _to_treys(hole)
    board_t = _to_treys(board)
    score = _EVAL.evaluate(board_t, hero)
    rank_class = _EVAL.get_rank_class(score)
    return _EVAL.class_to_string(rank_class)


def pot_odds_pct(pot: float, to_call: float) -> float | None:
    """Required equity to break even on a call, expressed as a percentage."""
    if to_call <= 0:
        return None
    denom = pot + 2 * to_call
    if denom <= 0:
        return None
    return to_call / denom * 100.0
