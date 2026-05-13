from __future__ import annotations

import time

from api.ai_provider import chat_ai_messages
from api.browser_automation import browser_operator
from terminal.service import terminal_service
from vision.screenshot import capture_screen


def execute_node(node: dict, state: dict) -> dict:
    node_type = str(node.get("type") or "note").lower()
    config = node.get("config") or {}
    started = time.perf_counter()
    try:
        if node_type == "terminal":
            job = terminal_service.run_sync(str(config.get("command") or ""), cwd=config.get("cwd") or None, timeout=int(config.get("timeout") or 180))
            result = job.as_dict()
            ok = result.get("status") == "completed"
        elif node_type == "browser":
            result = browser_operator.run_async(str(config.get("command") or "summarize page"))
            ok = bool(result.get("accepted", True))
        elif node_type == "vision":
            result = capture_screen()
            ok = bool(result.get("ok"))
        elif node_type == "ai":
            prompt = str(config.get("prompt") or state.get("lastText") or "")
            response = chat_ai_messages([{"role": "user", "content": prompt}], task_type=str(config.get("taskType") or "chat"))
            result = {"response": response}
            ok = True
        elif node_type == "wait":
            seconds = min(max(float(config.get("seconds") or 1), 0), 60)
            time.sleep(seconds)
            result = {"waitedSeconds": seconds}
            ok = True
        elif node_type == "condition":
            key = str(config.get("key") or "lastOk")
            expected = config.get("equals", True)
            ok = state.get(key) == expected
            result = {"key": key, "expected": expected, "actual": state.get(key)}
        else:
            result = {"message": str(config.get("text") or node.get("label") or "No-op node recorded.")}
            ok = True
        state["lastResult"] = result
        state["lastOk"] = ok
        if isinstance(result, dict):
            state["lastText"] = result.get("response") or result.get("stdout") or result.get("message") or state.get("lastText", "")
        return {"ok": ok, "nodeId": node["id"], "type": node_type, "result": result, "latencyMs": _elapsed(started)}
    except Exception as error:
        state["lastOk"] = False
        return {"ok": False, "nodeId": node.get("id"), "type": node_type, "error": str(error), "latencyMs": _elapsed(started)}


def _elapsed(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)
