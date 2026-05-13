from __future__ import annotations

from agents.base import AgentResult, BaseAgent
from planner.engine import PlanStep, TaskState
from workflows.workflow_engine import execute_workflow_graph
from workflows.workflow_store import list_workflow_definitions, load_workflow_definition, save_workflow_definition


class WorkflowAgent(BaseAgent):
    name = "workflow"

    def run(self, step: PlanStep, state: TaskState) -> AgentResult:
        if step.tool == "list_workflows":
            workflows = list_workflow_definitions()
            state.artifacts["workflows"] = workflows
            return AgentResult(True, f"Found {len(workflows)} saved workflow graph(s).", {"workflows": workflows})
        if step.tool == "run_workflow":
            workflow_id = _match_workflow_id(state.graph.goal)
            workflow = load_workflow_definition(workflow_id) if workflow_id else None
            if not workflow:
                return AgentResult(False, "No saved workflow matched the goal.", {"workflowId": workflow_id})
            result = execute_workflow_graph(workflow)
            state.artifacts["workflowRun"] = result
            return AgentResult(bool(result.get("ok")), "Workflow graph executed." if result.get("ok") else "Workflow graph failed.", result)
        if step.tool == "create_basic_workflow":
            workflow = {
                "name": "Generated Jarvis Workflow",
                "nodes": [
                    {"id": "vision", "type": "vision", "label": "Capture screen"},
                    {"id": "reason", "type": "ai", "label": "Reason", "config": {"prompt": state.graph.goal}},
                ],
                "edges": [{"from": "vision", "to": "reason"}],
            }
            result = save_workflow_definition(workflow)
            return AgentResult(bool(result.get("ok")), "Reusable workflow graph saved." if result.get("ok") else result.get("error", "Workflow save failed."), result)
        return AgentResult(False, f"WorkflowAgent does not support tool {step.tool}.")


def _match_workflow_id(goal: str) -> str:
    import re

    match = re.search(r"workflow\s+([a-zA-Z0-9_-]+)", goal)
    return match.group(1) if match else ""
