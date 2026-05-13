from __future__ import annotations

from datetime import datetime


def build_execution_report(result: dict) -> str:
    lines = ["# Jarvis Execution Report", "", f"Generated: {datetime.now().isoformat(timespec='seconds')}", "", f"Status: {'OK' if result.get('ok') else 'FAILED'}", ""]
    lines.append("## Response")
    lines.append(str(result.get("response") or result.get("result", {}).get("response") or ""))
    return "\n".join(lines)
