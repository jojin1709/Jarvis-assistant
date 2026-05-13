from __future__ import annotations

from planner.engine import TaskGraph, build_task_graph


def build_langgraph_or_local(goal: str):
    """Build a LangGraph StateGraph when installed; otherwise return Jarvis TaskGraph.

    The local graph keeps Jarvis runnable offline. When `langgraph` is installed,
    this adapter exposes the same planning state through a StateGraph entrypoint.
    """
    try:
        from langgraph.graph import END, StateGraph
    except Exception:
        return build_task_graph(goal)

    def plan_node(state: dict) -> dict:
        graph = build_task_graph(str(state["goal"]))
        return {**state, "graph": graph.as_dict()}

    workflow = StateGraph(dict)
    workflow.add_node("plan", plan_node)
    workflow.set_entry_point("plan")
    workflow.add_edge("plan", END)
    return workflow.compile()


def build_planning_artifact(goal: str) -> TaskGraph | object:
    return build_langgraph_or_local(goal)
