from pathlib import Path

from agents.base import AgentResult, BaseAgent
from devops.service_manager import docker_status, environment_report
from planner.engine import PlanStep, TaskState
from terminal.service import terminal_service


class DevOpsAgent(BaseAgent):
    name = "devops"

    def run(self, step: PlanStep, state: TaskState) -> AgentResult:
        project = state.artifacts.get("project") or {}
        project_path = project.get("path")
        if step.tool in {"install_dependencies", "verify_build"} and not project_path:
            return AgentResult(False, "No project path is available for DevOps step.")

        if step.tool == "install_dependencies":
            commands = project.get("installCommands") or []
            results = [terminal_service.run_sync(command, cwd=project_path, timeout=300).as_dict() for command in commands]
            state.artifacts["installResults"] = results
            ok = all(item.get("status") == "completed" for item in results)
            return AgentResult(ok, "Dependency installation complete." if ok else "Dependency installation failed or was blocked.", {"results": results})

        if step.tool == "verify_build":
            commands = project.get("verifyCommands") or []
            results = [terminal_service.run_sync(command, cwd=project_path, timeout=300).as_dict() for command in commands]
            state.artifacts["verifyResults"] = results
            ok = all(item.get("status") == "completed" for item in results)
            return AgentResult(ok, "Build verification passed." if ok else "Build verification found errors.", {"results": results})

        if step.tool == "environment_report":
            report = environment_report()
            state.artifacts["environment"] = report
            return AgentResult(True, "DevOps environment inspected.", report)

        if step.tool == "docker_status":
            status = docker_status()
            state.artifacts["docker"] = status
            return AgentResult(bool(status.get("available")), "Docker status captured." if status.get("available") else status.get("message", "Docker unavailable."), status)

        if step.tool == "general_execute":
            job = terminal_service.run_sync(state.graph.goal, cwd=Path.cwd(), timeout=180)
            return AgentResult(job.status == "completed", job.stdout or job.stderr or job.status, job.as_dict())

        return AgentResult(False, f"DevOpsAgent does not support tool {step.tool}.")
