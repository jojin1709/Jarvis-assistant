import re

from agents.base import AgentResult, BaseAgent
from planner.engine import PlanStep, TaskState
from workflows.recon import run_bug_bounty_workflow


class ReconAgent(BaseAgent):
    name = "recon"

    def run(self, step: PlanStep, state: TaskState) -> AgentResult:
        if step.tool == "scope":
            target = _extract_target(state.graph.goal)
            if not target:
                return AgentResult(False, "No valid target domain or URL was found in the request.")
            state.artifacts["target"] = target
            return AgentResult(True, f"Target scope set to {target}.", {"target": target})

        if step.tool == "bug_bounty_recon":
            target = str(state.artifacts.get("target") or _extract_target(state.graph.goal))
            result = run_bug_bounty_workflow(target)
            state.artifacts["recon"] = result
            return AgentResult(bool(result.get("ok")), f"Recon workflow complete for {target}." if result.get("ok") else str(result.get("error")), result)

        if step.tool == "analyze_findings":
            recon = state.artifacts.get("recon") or {}
            findings = recon.get("findings") or []
            return AgentResult(True, f"Analyzed recon output: {len(findings)} potential finding(s).", {"findings": findings})

        return AgentResult(False, f"ReconAgent does not support tool {step.tool}.")


def _extract_target(goal: str) -> str:
    match = re.search(r"(?:https?://)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})(?:/[^\s]*)?", goal)
    return match.group(0) if match else ""
