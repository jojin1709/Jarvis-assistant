from __future__ import annotations


def running_processes(limit: int = 120) -> list[dict]:
    try:
        import psutil

        rows = []
        for proc in psutil.process_iter(["pid", "name", "username", "cpu_percent", "memory_percent"]):
            info = proc.info
            rows.append({"pid": info.get("pid"), "name": info.get("name"), "user": info.get("username"), "cpu": info.get("cpu_percent"), "memory": round(info.get("memory_percent") or 0, 2)})
            if len(rows) >= limit:
                break
        return rows
    except Exception:
        return []
