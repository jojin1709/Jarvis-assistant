from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence


@dataclass
class ProviderResult:
    ok: bool
    provider: str
    response: str = ""
    error: str = ""
    latency_ms: int = 0
    source: str = "browser"
    metadata: dict = field(default_factory=dict)


class BrowserAIProvider:
    id = "browser"
    label = "Browser AI"
    url = ""
    login_url = ""
    prompt_selectors: Sequence[str] = ()
    submit_selectors: Sequence[str] = ()
    response_selectors: Sequence[str] = ()
    logged_out_markers: Sequence[str] = ("log in", "sign in")

    def __init__(self, session_manager) -> None:
        self.session_manager = session_manager

    async def ask(self, prompt: str, timeout_ms: int = 120000) -> ProviderResult:
        started = time.perf_counter()
        context = None
        try:
            context = await self.session_manager.open_context(self.id)
            page = await self.session_manager.primary_page(context)
            await page.goto(self.url, wait_until="domcontentloaded", timeout=45000)
            await self._recover_page(page)
            if await self.is_login_required(page):
                return ProviderResult(
                    ok=False,
                    provider=self.id,
                    error=f"{self.label} needs manual login. Open the provider login session, sign in, then retry.",
                    latency_ms=_elapsed(started),
                    metadata={"loginRequired": True, "loginUrl": self.login_url or self.url},
                )

            prompt_box = await self._first_visible(page, self.prompt_selectors, timeout_ms=25000)
            before = await self._latest_response_text(page)
            await self._fill_prompt(prompt_box, prompt)
            await self._submit(page, prompt_box)
            response = await self._wait_for_response(page, before=before, timeout_ms=timeout_ms)
            return ProviderResult(ok=True, provider=self.id, response=response, latency_ms=_elapsed(started))
        except Exception as error:
            return ProviderResult(ok=False, provider=self.id, error=str(error), latency_ms=_elapsed(started))
        finally:
            if context is not None:
                await self.session_manager.close_context(self.id, context)

    async def open_login(self) -> ProviderResult:
        context = await self.session_manager.open_context(self.id, keep_open=True)
        page = await self.session_manager.primary_page(context)
        await page.goto(self.login_url or self.url, wait_until="domcontentloaded", timeout=45000)
        return ProviderResult(
            ok=True,
            provider=self.id,
            response=f"{self.label} login window opened. Sign in manually; Jarvis will reuse this persistent profile.",
            metadata={"loginUrl": page.url},
        )

    async def status(self) -> dict:
        profile = self.session_manager.profile_dir(self.id)
        return {
            "id": self.id,
            "label": self.label,
            "source": "browser",
            "profilePath": str(profile),
            "profileExists": profile.exists(),
            "loginUrl": self.login_url or self.url,
        }

    async def is_login_required(self, page) -> bool:
        url = page.url.lower()
        if any(marker in url for marker in ("login", "auth", "signin", "sign-in")):
            return True
        text = (await _safe_inner_text(page, "body"))[:5000].lower()
        return any(marker in text for marker in self.logged_out_markers) and not await self._has_prompt(page)

    async def _recover_page(self, page) -> None:
        await page.wait_for_load_state("domcontentloaded", timeout=30000)
        await asyncio.sleep(1.0)

    async def _has_prompt(self, page) -> bool:
        for selector in self.prompt_selectors:
            locator = page.locator(selector).last
            try:
                if await locator.count() and await locator.is_visible(timeout=800):
                    return True
            except Exception:
                continue
        return False

    async def _first_visible(self, page, selectors: Sequence[str], timeout_ms: int = 10000):
        deadline = time.monotonic() + timeout_ms / 1000
        last_error = None
        while time.monotonic() < deadline:
            for selector in selectors:
                try:
                    locator = page.locator(selector).last
                    if await locator.count() and await locator.is_visible(timeout=800):
                        return locator
                except Exception as error:
                    last_error = error
            await asyncio.sleep(0.35)
        raise RuntimeError(f"No visible prompt field found for {self.label}. {last_error or ''}".strip())

    async def _fill_prompt(self, locator, prompt: str) -> None:
        try:
            await locator.click(timeout=5000)
            await locator.fill(prompt, timeout=12000)
            return
        except Exception:
            pass
        await locator.click(timeout=5000)
        await locator.press("Control+A")
        await locator.type(prompt, delay=2, timeout=30000)

    async def _submit(self, page, prompt_locator) -> None:
        for selector in self.submit_selectors:
            try:
                button = page.locator(selector).last
                if await button.count() and await button.is_enabled(timeout=1000):
                    await button.click(timeout=5000)
                    return
            except Exception:
                continue
        await prompt_locator.press("Enter")

    async def _wait_for_response(self, page, before: str, timeout_ms: int) -> str:
        deadline = time.monotonic() + timeout_ms / 1000
        stable_seen = 0
        last_text = ""
        while time.monotonic() < deadline:
            text = await self._latest_response_text(page)
            if text and text != before and len(text) >= max(8, min(80, len(before))):
                if text == last_text:
                    stable_seen += 1
                else:
                    stable_seen = 0
                    last_text = text
                if stable_seen >= 3 and not await self._is_generating(page):
                    return _clean_response(text)
            await asyncio.sleep(1.0)
        if last_text:
            return _clean_response(last_text)
        raise RuntimeError(f"{self.label} did not produce a readable response before timeout.")

    async def _latest_response_text(self, page) -> str:
        candidates: list[str] = []
        for selector in self.response_selectors:
            try:
                locators = page.locator(selector)
                count = await locators.count()
                if not count:
                    continue
                text = await locators.nth(count - 1).inner_text(timeout=2500)
                if text.strip():
                    candidates.append(text)
            except Exception:
                continue
        return max(candidates, key=len) if candidates else ""

    async def _is_generating(self, page) -> bool:
        generating_selectors = (
            "button[aria-label*='Stop' i]",
            "button:has-text('Stop')",
            "[data-testid='stop-button']",
            "[aria-label*='Stop generating' i]",
        )
        for selector in generating_selectors:
            try:
                locator = page.locator(selector).first
                if await locator.count() and await locator.is_visible(timeout=500):
                    return True
            except Exception:
                continue
        return False


async def _safe_inner_text(page, selector: str) -> str:
    try:
        return await page.locator(selector).inner_text(timeout=2500)
    except Exception:
        return ""


def _clean_response(text: str) -> str:
    compact = re.sub(r"\n{3,}", "\n\n", text).strip()
    return compact


def _elapsed(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)
