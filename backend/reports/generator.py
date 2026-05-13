from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from api.memory_storage import configured_memory_root, remember_event


@dataclass
class VulnerabilityFinding:
    title: str
    severity: str
    affected_asset: str
    evidence: str
    reproduction_steps: list[str]
    impact: str
    remediation: str
    cvss: str = "Not calculated"


def write_bug_bounty_report(target: str, findings: list[VulnerabilityFinding], notes: list[str] | None = None) -> dict:
    report_dir = configured_memory_root() / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    safe_target = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in target)[:80].strip("-") or "target"
    path = report_dir / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{safe_target}-report.md"
    content = render_bug_bounty_report(target, findings, notes or [])
    path.write_text(content, encoding="utf-8", newline="\n")
    remember_event("logs", f"Bug bounty report: {target}", content[:12000], {"path": str(path), "findings": len(findings)})
    return {"path": str(path), "content": content, "findingCount": len(findings)}


def render_bug_bounty_report(target: str, findings: list[VulnerabilityFinding], notes: list[str]) -> str:
    lines = [
        f"# Vulnerability Report: {target}",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Executive Summary",
        "",
        f"Jarvis analyzed the target and identified {len(findings)} potential finding(s).",
        "",
        "## Scope",
        "",
        f"- Target: `{target}`",
        "- Testing mode: authorized-assessment workflow",
        "",
    ]
    if notes:
        lines.extend(["## Recon Notes", ""])
        lines.extend(f"- {note}" for note in notes)
        lines.append("")

    if not findings:
        lines.extend(["## Findings", "", "No actionable vulnerabilities were confirmed from the available tool output.", ""])
        return "\n".join(lines)

    lines.extend(["## Findings", ""])
    for index, finding in enumerate(findings, start=1):
        lines.extend(
            [
                f"### {index}. {finding.title}",
                "",
                f"**Severity:** {finding.severity}",
                f"**CVSS:** {finding.cvss}",
                f"**Affected asset:** `{finding.affected_asset}`",
                "",
                "#### Evidence",
                "",
                "```text",
                finding.evidence.strip()[:4000],
                "```",
                "",
                "#### Reproduction Steps",
                "",
            ]
        )
        lines.extend(f"{step_number}. {step}" for step_number, step in enumerate(finding.reproduction_steps, start=1))
        lines.extend(
            [
                "",
                "#### Impact",
                "",
                finding.impact,
                "",
                "#### Remediation",
                "",
                finding.remediation,
                "",
            ]
        )
    return "\n".join(lines)
