from __future__ import annotations

import socket
from contextlib import closing


def network_state() -> dict:
    checks = []
    for host, port in (("1.1.1.1", 53), ("8.8.8.8", 53)):
        checks.append(_connectivity_check(host, port))
    return {"online": any(item["ok"] for item in checks), "checks": checks, "activePorts": active_ports()}


def active_ports(limit: int = 80) -> list[dict]:
    try:
        import psutil

        rows = []
        for conn in psutil.net_connections(kind="inet")[:limit]:
            if conn.laddr:
                rows.append({"local": f"{conn.laddr.ip}:{conn.laddr.port}", "remote": f"{getattr(conn.raddr, 'ip', '')}:{getattr(conn.raddr, 'port', '')}" if conn.raddr else "", "status": conn.status, "pid": conn.pid})
        return rows
    except Exception:
        return []


def _connectivity_check(host: str, port: int) -> dict:
    try:
        with closing(socket.create_connection((host, port), timeout=2)):
            return {"host": host, "port": port, "ok": True}
    except OSError as error:
        return {"host": host, "port": port, "ok": False, "error": str(error)}
