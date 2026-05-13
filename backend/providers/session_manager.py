from __future__ import annotations

import asyncio
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Awaitable, TypeVar


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROFILE_ROOT = BACKEND_DIR / "profiles"
LOG_PATH = BACKEND_DIR / "runtime" / "provider-orchestration" / "provider-events.jsonl"
PROFILE_NAMES = {"chatgpt_web": "chatgpt", "claude_web": "claude", "gemini_web": "gemini"}

T = TypeVar("T")


class ProviderSessionManager:
    def __init__(self) -> None:
        self.profile_root = PROFILE_ROOT
        self.profile_root.mkdir(parents=True, exist_ok=True)
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._locks: dict[str, asyncio.Lock] = {}
        self._kept_contexts: dict[str, object] = {}
        self._playwright = None

    def run(self, coro: Awaitable[T]) -> T:
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    def profile_dir(self, provider: str) -> Path:
        path = self.profile_root / PROFILE_NAMES.get(provider, provider)
        path.mkdir(parents=True, exist_ok=True)
        return path

    async def open_context(self, provider: str, keep_open: bool = False):
        if provider in self._kept_contexts:
            return self._kept_contexts[provider]
        lock = self._locks.setdefault(provider, asyncio.Lock())
        await lock.acquire()
        try:
            playwright = await self._ensure_playwright()
            context = await playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.profile_dir(provider)),
                headless=False,
                viewport={"width": 1366, "height": 860},
                accept_downloads=False,
            )
            context.on("close", lambda *_args, provider=provider, context=context: self._context_closed(provider, context))
            if keep_open:
                self._kept_contexts[provider] = context
            return context
        except Exception:
            lock.release()
            raise

    async def close_context(self, provider: str, context) -> None:
        kept = self._kept_contexts.get(provider)
        if kept is context:
            return
        try:
            await context.close()
        finally:
            lock = self._locks.get(provider)
            if lock and lock.locked():
                lock.release()

    async def close_kept_context(self, provider: str) -> None:
        context = self._kept_contexts.pop(provider, None)
        if context:
            try:
                await context.close()
            finally:
                lock = self._locks.get(provider)
                if lock and lock.locked():
                    lock.release()

    async def primary_page(self, context):
        if context.pages:
            return context.pages[0]
        return await context.new_page()

    def log_event(self, event: dict) -> None:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        payload = {"createdAt": datetime.now().isoformat(timespec="seconds"), **event}
        with LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def recent_events(self, limit: int = 80) -> list[dict]:
        if not LOG_PATH.exists():
            return []
        lines = LOG_PATH.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]
        events = []
        for line in lines:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return list(reversed(events))

    async def _ensure_playwright(self):
        if self._playwright:
            return self._playwright
        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()
        return self._playwright

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def _context_closed(self, provider: str, context) -> None:
        if self._kept_contexts.get(provider) is context:
            self._kept_contexts.pop(provider, None)
        lock = self._locks.get(provider)
        if lock and lock.locked():
            lock.release()


session_manager = ProviderSessionManager()
