"""GameState — what the agents see at every decision point."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Street = Literal["preflop", "flop", "turn", "river"]
Position = Literal["BTN", "SB", "BB", "UTG", "MP", "CO"]


@dataclass
class GameState:
    hole_cards: list[str] = field(default_factory=list)
    board: list[str] = field(default_factory=list)
    num_opponents: int = 1
    pot: float = 0.0
    to_call: float = 0.0
    hero_stack: float = 100.0
    position: Position = "BTN"
    action_history: list[str] = field(default_factory=list)

    @property
    def street(self) -> Street:
        n = len(self.board)
        if n == 0:
            return "preflop"
        if n == 3:
            return "flop"
        if n == 4:
            return "turn"
        if n == 5:
            return "river"
        raise ValueError(f"Invalid board length: {n}")

    def summary(self) -> str:
        from .cards import pretty

        hero = " ".join(pretty(c) for c in self.hole_cards) or "?"
        board = " ".join(pretty(c) for c in self.board) or "(none)"
        return (
            f"Street: {self.street}\n"
            f"Hero: {hero}\n"
            f"Board: {board}\n"
            f"Opponents: {self.num_opponents}\n"
            f"Pot: {self.pot:g}, To call: {self.to_call:g}, "
            f"Hero stack: {self.hero_stack:g}\n"
            f"Position: {self.position}\n"
            f"Action so far: {', '.join(self.action_history) or '(none)'}"
        )
