from __future__ import annotations

import json
from datetime import datetime

from app.config import BACKEND_DIR
from telemetry.crash_reporter import crash_summary
from telemetry.diagnostics_collector import diagnostics_snapshot
from telemetry.execution_metrics import execution_metrics
from telemetry.performance_tracker import performance_snapshot


CONFIG_PATH = BACKEND_DIR / "runtime" / "telemetry" / "config.json"


def telemetry_config() -> dict:
    if not CONFIG_PATH.exists():
        return {"enabled": False, "shareDiagnostics": False, "retentionDays": 14}
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return {"enabled": False, "shareDiagnostics": False, "retentionDays": 14, **data}
    except json.JSONDecodeError:
        return {"enabled": False, "shareDiagnostics": False, "retentionDays": 14}


def update_telemetry_config(patch: dict) -> dict:
    config = telemetry_config()
    config.update({key: patch[key] for key in ("enabled", "shareDiagnostics", "retentionDays") if key in patch})
    config["updatedAt"] = datetime.now().isoformat(timespec="seconds")
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return config


def analytics_snapshot() -> dict:
    config = telemetry_config()
    local = {"execution": execution_metrics(), "performance": performance_snapshot(), "crashes": crash_summary()}
    return {"config": config, "localOnly": not config.get("shareDiagnostics"), "metrics": local}


def diagnostic_bundle() -> dict:
    config = telemetry_config()
    if not config.get("enabled"):
        return {"ok": False, "message": "Telemetry is disabled.", "config": config}
    return {"ok": True, "config": config, "diagnostics": diagnostics_snapshot()}
