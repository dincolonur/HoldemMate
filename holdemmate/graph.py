"""LangGraph workflow that wires the agents together.

The Strategy agent now produces both the action and the coaching note in one
Claude call (see `strategy_agent.run_strategy`), so the workflow is:

    START → math → opponent → strategy → END
"""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from .agents.math_agent import run_math
from .agents.opponent_agent import run_opponent
from .agents.strategy_agent import run_strategy
from .game_state import GameState


class WorkflowState(TypedDict, total=False):
    game: GameState
    math: dict[str, Any]
    opponent: dict[str, Any]
    strategy: dict[str, Any]


def _math_node(state: WorkflowState) -> WorkflowState:
    return {"math": run_math(state["game"])}


def _opponent_node(state: WorkflowState) -> WorkflowState:
    return {"opponent": run_opponent(state["game"], state["math"])}


def _strategy_node(state: WorkflowState) -> WorkflowState:
    return {"strategy": run_strategy(state["game"], state["math"], state["opponent"])}


def build_graph():
    graph = StateGraph(WorkflowState)
    graph.add_node("math", _math_node)
    graph.add_node("opponent", _opponent_node)
    graph.add_node("strategy", _strategy_node)

    graph.add_edge(START, "math")
    graph.add_edge("math", "opponent")
    graph.add_edge("opponent", "strategy")
    graph.add_edge("strategy", END)

    return graph.compile()


def recommend(game: GameState) -> dict[str, Any]:
    """Run the full pipeline and return everything the UI needs.

    The returned dict has the same shape as before: a top-level `coach` key
    is included for backwards compatibility with the UI, pulled from the
    merged strategy response.
    """
    workflow = build_graph()
    final: WorkflowState = workflow.invoke({"game": game})
    strategy = final.get("strategy", {}) or {}
    return {
        "math": final.get("math"),
        "opponent": final.get("opponent"),
        "strategy": strategy,
        "coach": strategy.get("coaching_note", strategy.get("rationale", "")),
    }
