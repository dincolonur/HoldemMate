"""LangGraph workflow that wires the four agents together."""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from .agents.coach_agent import run_coach
from .agents.math_agent import run_math
from .agents.opponent_agent import run_opponent
from .agents.strategy_agent import run_strategy
from .game_state import GameState


class WorkflowState(TypedDict, total=False):
    game: GameState
    math: dict[str, Any]
    opponent: dict[str, Any]
    strategy: dict[str, Any]
    coach: str


def _math_node(state: WorkflowState) -> WorkflowState:
    return {"math": run_math(state["game"])}


def _opponent_node(state: WorkflowState) -> WorkflowState:
    return {"opponent": run_opponent(state["game"], state["math"])}


def _strategy_node(state: WorkflowState) -> WorkflowState:
    return {"strategy": run_strategy(state["game"], state["math"], state["opponent"])}


def _coach_node(state: WorkflowState) -> WorkflowState:
    return {
        "coach": run_coach(
            state["game"], state["math"], state["opponent"], state["strategy"]
        )
    }


def build_graph():
    graph = StateGraph(WorkflowState)
    graph.add_node("math", _math_node)
    graph.add_node("opponent", _opponent_node)
    graph.add_node("strategy", _strategy_node)
    graph.add_node("coach", _coach_node)

    graph.add_edge(START, "math")
    graph.add_edge("math", "opponent")
    graph.add_edge("opponent", "strategy")
    graph.add_edge("strategy", "coach")
    graph.add_edge("coach", END)

    return graph.compile()


def recommend(game: GameState) -> dict[str, Any]:
    """Run the full pipeline and return everything the UI needs."""
    workflow = build_graph()
    final: WorkflowState = workflow.invoke({"game": game})
    return {
        "math": final.get("math"),
        "opponent": final.get("opponent"),
        "strategy": final.get("strategy"),
        "coach": final.get("coach"),
    }
