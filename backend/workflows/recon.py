from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from urllib.parse import urlparse

from api.memory_storage import configured_memory_root, remember_event
from reports.generator import VulnerabilityFinding, write_bug_bounty_report
from terminal.service import terminal_service


RECON_TOOLS = ("subfinder", "amass", "httpx", "nuclei", "ffuf", "katana", "gau", "trufflehog", "naabu")


def run_bug_bounty_workflow(target: str) -> dict:
    normalized = _normalize_target(target)
    if not normalized:
        return {"ok": False, "error": "A valid target domain or URL is required."}

    workspace = configured_memory_root() / "bug-bounty" / _safe_name(normalized)
    workspace.mkdir(parents=True, exist_ok=True)
    available = {tool: shutil.which(tool) for tool in RECON_TOOLS}
    commands = _commands(normalized, workspace, available)

    results = []
    for label, command in commands:
        job = terminal_service.run_sync(command, cwd=workspace, timeout=900)
        results.append({"label": label, **job.as_dict()})

    findings = analyze_recon_results(normalized, workspace, results)
    report = write_bug_bounty_report(
        normalized,
        findings,
        notes=[
            f"Available tools: {', '.join(tool for tool, path in available.items() if path) or 'none detected'}",
            f"Workspace: {workspace}",
        ],
    )
    remember_event("workflows", f"Bug bounty workflow: {normalized}", json.dumps({"results": results, "report": report["path"]})[:12000], {"target": normalized})
    return {"ok": True, "target": normalized, "workspace": str(workspace), "results": results, "findings": [finding.__dict__ for finding in findings], "report": report}


def analyze_recon_results(target: str, workspace: Path, results: list[dict]) -> list[VulnerabilityFinding]:
    findings: list[VulnerabilityFinding] = []
    combined = "\n".join(str(item.get("stdout") or item.get("stderr") or "") for item in results)
    if "critical" in combined.lower() or "high" in combined.lower():
        findings.append(
            VulnerabilityFinding(
                title="High-severity scanner output requires manual validation",
                severity="High",
                affected_asset=target,
                evidence=_excerpt(combined, ("critical", "high")),
                reproduction_steps=["Review the nuclei output in the recon workspace.", "Manually reproduce the matched template against the affected endpoint.", "Confirm impact without destructive actions."],
                impact="Scanner output indicates a potentially high-impact issue. Manual validation is required before submission.",
                remediation="Patch the affected software or configuration according to the confirmed template and vendor guidance.",
            )
        )

    urls = _read_lines(workspace / "urls.txt")
    interesting = [url for url in urls if any(marker in url.lower() for marker in ("admin", "debug", "backup", "test", "dev", "staging", "api"))]
    if interesting:
        findings.append(
            VulnerabilityFinding(
                title="Interesting exposed endpoints discovered",
                severity="Informational",
                affected_asset=target,
                evidence="\n".join(interesting[:25]),
                reproduction_steps=["Open the listed endpoints in a browser.", "Check whether sensitive functions or debug data are exposed.", "Validate access controls with only authorized accounts."],
                impact="Exposed administrative, debug, or staging endpoints may increase attack surface.",
                remediation="Restrict sensitive endpoints, remove debug routes, and enforce authentication.",
            )
        )
    return findings


def _commands(target: str, workspace: Path, available: dict[str, str | None]) -> list[tuple[str, str]]:
    commands: list[tuple[str, str]] = []
    domain = target.replace("https://", "").replace("http://", "").split("/")[0]
    if available.get("subfinder"):
        commands.append(("subfinder", f"subfinder -silent -d {domain} -o subdomains.txt"))
    elif available.get("amass"):
        commands.append(("amass", f"amass enum -passive -d {domain} -o subdomains.txt"))

    if available.get("httpx"):
        commands.append(("httpx", "httpx -silent -l subdomains.txt -o live-hosts.txt"))
    if available.get("gau"):
        commands.append(("gau", f"gau {domain} --o urls.txt"))
    if available.get("katana"):
        commands.append(("katana", f"katana -silent -u https://{domain} -o urls.txt"))
    if available.get("nuclei"):
        input_file = "live-hosts.txt" if (workspace / "live-hosts.txt").exists() else "subdomains.txt"
        commands.append(("nuclei", f"nuclei -silent -l {input_file} -o nuclei.txt"))
    if available.get("trufflehog"):
        commands.append(("trufflehog", f"trufflehog git https://{domain} --json"))
    if not commands:
        (workspace / "notes.txt").write_text("No supported recon tools were detected on PATH.\n", encoding="utf-8")
    return commands


def _normalize_target(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    host = parsed.netloc or parsed.path
    if not re.match(r"^[a-zA-Z0-9.-]+$", host):
        return ""
    return host.strip(".").lower()


def _safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in value)[:80]


def _read_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip()]


def _excerpt(text: str, markers: tuple[str, ...]) -> str:
    lines = text.splitlines()
    selected = [line for line in lines if any(marker in line.lower() for marker in markers)]
    return "\n".join(selected[:30]) or text[:2000]
