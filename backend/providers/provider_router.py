from __future__ import annotations

import concurrent.futures
import json
import time
from dataclasses import asdict
from pathlib import Path

from providers.base_provider import ProviderResult
from providers.chatgpt_provider import ChatGPTBrowserProvider
from providers.claude_provider import ClaudeBrowserProvider
from providers.config import load_provider_config
from providers.gemini_provider import GeminiBrowserProvider
from providers.session_manager import session_manager


HISTORY_PATH = Path(__file__).resolve().parents[1] / "runtime" / "provider-orchestration" / "history.jsonl"


def browser_provider_instances() -> dict[str, object]:
    return {
        "chatgpt_web": ChatGPTBrowserProvider(session_manager),
        "claude_web": ClaudeBrowserProvider(session_manager),
        "gemini_web": GeminiBrowserProvider(session_manager),
    }


def browser_provider_status() -> dict:
    providers = browser_provider_instances()
    browser_config = load_provider_config().get("browser_providers", {})
    enabled_map = browser_config.get("enabled_providers", {})
    statuses = []
    for provider_id, provider in providers.items():
        status = session_manager.run(provider.status())
        status["enabled"] = bool(enabled_map.get(provider_id, False))
        statuses.append(status)
    return {
        "providers": statuses,
        "history": recent_history(),
        "events": session_manager.recent_events(),
        "config": browser_config,
    }


def open_provider_login(provider_id: str) -> ProviderResult:
    provider = browser_provider_instances().get(provider_id)
    if not provider:
        return ProviderResult(ok=False, provider=provider_id, error="Unsupported browser provider.")
    result = session_manager.run(provider.open_login())
    _record(result, prompt="[manual-login]")
    return result


def ask_with_orchestration(
    messages: list[dict[str, str]],
    task_type: str = "chat",
    preferred_provider: str | None = None,
    multi_provider: bool | None = None,
) -> ProviderResult:
    config = load_provider_config()
    browser_config = config.get("browser_providers", {})
    if not browser_config.get("enabled", False):
        return ProviderResult(ok=False, provider="orchestrator", error="Browser provider orchestration is disabled.")

    prompt = _messages_to_prompt(messages)
    provider_ids = _route_candidates(task_type, preferred_provider, browser_config)
    if multi_provider is None:
        multi_provider = bool(browser_config.get("multi_provider", False))
    if multi_provider:
        result = _ask_many(provider_ids, prompt)
    else:
        result = _ask_first(provider_ids, prompt)
    _record(result, prompt=prompt[:2000], task_type=task_type)
    return result


def aggregate_responses(results: list[ProviderResult]) -> ProviderResult:
    successful = [result for result in results if result.ok and result.response.strip()]
    if not successful:
        errors = " | ".join(result.error for result in results if result.error)
        return ProviderResult(ok=False, provider="multi_provider", error=errors or "No browser provider returned a response.")

    if len(successful) == 1:
        only = successful[0]
        only.metadata["sources"] = [only.provider]
        return only

    merged = [
        "# Multi-provider synthesis",
        "",
        "Jarvis gathered responses from multiple browser AI providers and merged the strongest overlapping guidance.",
        "",
    ]
    for result in successful:
        merged.extend([f"## Source: {result.provider}", "", result.response.strip(), ""])
    return ProviderResult(
        ok=True,
        provider="multi_provider",
        response="\n".join(merged).strip(),
        latency_ms=max(result.latency_ms for result in successful),
        metadata={"sources": [result.provider for result in successful]},
    )


def recent_history(limit: int = 80) -> list[dict]:
    if not HISTORY_PATH.exists():
        return []
    lines = HISTORY_PATH.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]
    rows = []
    for line in lines:
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return list(reversed(rows))


def _ask_first(provider_ids: list[str], prompt: str) -> ProviderResult:
    providers = browser_provider_instances()
    errors = []
    for provider_id in provider_ids:
        provider = providers.get(provider_id)
        if not provider:
            continue
        result: ProviderResult = session_manager.run(provider.ask(prompt))
        session_manager.log_event({"provider": provider_id, "ok": result.ok, "latencyMs": result.latency_ms, "error": result.error})
        if result.ok:
            return result
        errors.append(f"{provider_id}: {result.error}")
    return ProviderResult(ok=False, provider="browser_router", error=" | ".join(errors) or "No browser provider was available.")


def _ask_many(provider_ids: list[str], prompt: str) -> ProviderResult:
    providers = browser_provider_instances()
    selected = [provider_id for provider_id in provider_ids if provider_id in providers][:3]
    if not selected:
        return ProviderResult(ok=False, provider="multi_provider", error="No browser providers are enabled for multi-provider mode.")
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(selected)) as executor:
        futures = [executor.submit(lambda item=provider_id: session_manager.run(providers[item].ask(prompt))) for provider_id in selected]
        results = [future.result() for future in futures]
    for result in results:
        session_manager.log_event({"provider": result.provider, "ok": result.ok, "latencyMs": result.latency_ms, "error": result.error})
    return aggregate_responses(results)


def _route_candidates(task_type: str, preferred_provider: str | None, browser_config: dict) -> list[str]:
    enabled = browser_config.get("enabled_providers") or {}
    if not isinstance(enabled, dict):
        enabled = {}
    routes = browser_config.get("routes") or {}
    configured = []
    if preferred_provider:
        configured.append(preferred_provider)
    route = str(routes.get(task_type) or routes.get("chat") or "").strip()
    if route and route != "auto":
        configured.append(route)
    defaults = {
        "coding": ["claude_web", "chatgpt_web", "gemini_web"],
        "reasoning": ["chatgpt_web", "claude_web", "gemini_web"],
        "research": ["gemini_web", "chatgpt_web", "claude_web"],
        "automation": ["chatgpt_web", "claude_web", "gemini_web"],
        "chat": ["chatgpt_web", "claude_web", "gemini_web"],
    }.get(task_type, ["chatgpt_web", "claude_web", "gemini_web"])
    configured.extend(defaults)
    result = []
    for provider_id in configured:
        if provider_id in result:
            continue
        if bool(enabled.get(provider_id, False)):
            result.append(provider_id)
    return result


def _messages_to_prompt(messages: list[dict[str, str]]) -> str:
    parts = []
    for message in messages:
        role = str(message.get("role") or "user").upper()
        content = str(message.get("content") or "").strip()
        if content:
            parts.append(f"{role}:\n{content}")
    return "\n\n".join(parts).strip()


def _record(result: ProviderResult, prompt: str, task_type: str = "chat") -> None:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "taskType": task_type,
        "prompt": prompt,
        "result": asdict(result),
    }
    with HISTORY_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
