from __future__ import annotations

import os
import queue
import shlex
import subprocess
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from api.permissions import evaluate_permission
from safety.policy import command_risk


ALLOWED_EXECUTABLES = {
    "npm",
    "npm.cmd",
    "npx",
    "npx.cmd",
    "pnpm",
    "pnpm.cmd",
    "yarn",
    "yarn.cmd",
    "node",
    "node.exe",
    "python",
    "python.exe",
    "py",
    "py.exe",
    "git",
    "git.exe",
    "docker",
    "docker.exe",
}


@dataclass
class TerminalJob:
    id: str
    command: str
    cwd: str
    status: str = "queued"
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    started_at: str = ""
    ended_at: str = ""

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "command": self.command,
            "cwd": self.cwd,
            "status": self.status,
            "exitCode": self.exit_code,
            "stdout": self.stdout[-20000:],
            "stderr": self.stderr[-12000:],
            "createdAt": self.created_at,
            "startedAt": self.started_at,
            "endedAt": self.ended_at,
        }


class TerminalService:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, TerminalJob] = {}
        self._processes: dict[str, subprocess.Popen] = {}
        self._queue: queue.Queue[str] = queue.Queue()
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()

    def run_sync(self, command: str, cwd: str | Path | None = None, timeout: int = 180) -> TerminalJob:
        job = self.enqueue(command, cwd)
        deadline = time.time() + timeout
        while time.time() < deadline:
            current = self.job(job.id)
            if current and current.status in {"completed", "failed", "cancelled", "blocked"}:
                return current
            time.sleep(0.2)
        self.cancel(job.id)
        current = self.job(job.id) or job
        current.status = "failed"
        current.stderr += "\nCommand timed out."
        return current

    def enqueue(self, command: str, cwd: str | Path | None = None) -> TerminalJob:
        resolved_cwd = str(Path(cwd or os.getcwd()).expanduser().resolve())
        job = TerminalJob(
            id=f"term-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            command=" ".join(str(command).strip().split()),
            cwd=resolved_cwd,
        )
        with self._lock:
            self._jobs[job.id] = job
        self._queue.put(job.id)
        return job

    def cancel(self, job_id: str) -> dict:
        with self._lock:
            process = self._processes.get(job_id)
            job = self._jobs.get(job_id)
        if process and process.poll() is None:
            _terminate_process_tree(process)
        if job:
            job.status = "cancelled"
            job.ended_at = datetime.now().isoformat(timespec="seconds")
            return job.as_dict()
        return {"error": "Terminal job not found."}

    def shutdown(self) -> list[dict]:
        with self._lock:
            running = list(self._processes.items())
        cancelled: list[dict] = []
        for job_id, process in running:
            if process.poll() is None:
                _terminate_process_tree(process)
            job = self.job(job_id)
            if job:
                job.status = "cancelled"
                job.ended_at = datetime.now().isoformat(timespec="seconds")
                job.stderr = (job.stderr + "\nCancelled because JX JARVIS closed.").strip()
                cancelled.append(job.as_dict())
        return cancelled

    def job(self, job_id: str) -> TerminalJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def history(self, limit: int = 80) -> list[dict]:
        with self._lock:
            jobs = list(self._jobs.values())[-limit:]
        return [job.as_dict() for job in reversed(jobs)]

    def _worker_loop(self) -> None:
        while True:
            job_id = self._queue.get()
            try:
                job = self.job(job_id)
                if job:
                    self._run_job(job)
            finally:
                self._queue.task_done()

    def _run_job(self, job: TerminalJob) -> None:
        decision = _authorize_command(job.command, job.cwd)
        if not decision["allowed"]:
            job.status = "blocked"
            job.stderr = str(decision["reason"])
            job.ended_at = datetime.now().isoformat(timespec="seconds")
            return

        job.status = "running"
        job.started_at = datetime.now().isoformat(timespec="seconds")
        args = _split_command(job.command)
        try:
            process = subprocess.Popen(
                args,
                cwd=job.cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            with self._lock:
                self._processes[job.id] = process
            stdout, stderr = process.communicate()
            job.stdout = stdout or ""
            job.stderr = stderr or ""
            job.exit_code = process.returncode
            job.status = "completed" if process.returncode == 0 else "failed"
        except FileNotFoundError as error:
            job.status = "failed"
            job.stderr = f"Command executable not found: {error}"
        except OSError as error:
            job.status = "failed"
            job.stderr = f"Command failed to start: {error}"
        finally:
            job.ended_at = datetime.now().isoformat(timespec="seconds")
            with self._lock:
                self._processes.pop(job.id, None)


def _authorize_command(command: str, cwd: str) -> dict:
    risk = command_risk(command)
    if not risk["allowed"]:
        return risk

    args = _split_command(command)
    if not args:
        return {"allowed": False, "reason": "Empty command."}
    executable = Path(args[0]).name.lower()
    if executable not in ALLOWED_EXECUTABLES:
        return {"allowed": False, "reason": f"Command executable is not allowed: {args[0]}"}

    decision = evaluate_permission("terminal.safe", f"run safe terminal command {command}", path=cwd, command=command)
    if not decision.allowed:
        return {"allowed": False, "reason": decision.message}
    if decision.requires_confirmation:
        return {"allowed": False, "reason": f"Confirmation required before running: {command}"}
    return {"allowed": True, "reason": "Allowed."}


def _split_command(command: str) -> list[str]:
    if os.name == "nt":
        return shlex.split(command, posix=False)
    return shlex.split(command)


def _terminate_process_tree(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/pid", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            return
        except OSError:
            pass
    try:
        process.terminate()
        process.wait(timeout=2)
    except Exception:
        try:
            process.kill()
        except Exception:
            pass


terminal_service = TerminalService()
