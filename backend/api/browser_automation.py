import re
import queue
import threading
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

from api.permissions import evaluate_permission, guard_action, log_activity
from api.memory_storage import remember_event
from automation.workflow_recorder import record_action


RUNTIME_DIR = Path(__file__).resolve().parents[1] / "runtime" / "browser"
SCREENSHOT_PATH = RUNTIME_DIR / "current.png"


class BrowserOperator:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._queue: queue.Queue[str] = queue.Queue()
        self._worker: threading.Thread | None = None
        self._stop_requested = False
        self._paused = False
        self._logs: list[dict[str, str]] = []
        self._history: list[dict[str, str]] = []
        self._state = {
            "status": "idle",
            "currentAction": "Ready",
            "currentUrl": "",
            "title": "Browser idle",
            "screenshotUrl": None,
            "screenshotToken": "",
            "domSummary": {"inputs": [], "buttons": [], "links": []},
            "tabs": [],
        }

    def state(self) -> dict:
        with self._lock:
            return {
                **self._state,
                "logs": list(reversed(self._logs[-80:])),
                "history": list(reversed(self._history[-40:])),
            }

    def run_async(self, text: str) -> dict:
        command = " ".join(text.strip().split())
        if not command:
            return {"accepted": False, "response": "Tell me what to do in the browser.", **self.state()}

        permission_action = self._permission_action(command)
        decision = evaluate_permission(permission_action, f"browser automation: {command}")
        if not decision.allowed:
            self._log(decision.message, "error")
            return {"accepted": False, "response": decision.message, **self.state()}

        with self._lock:
            if self._state["status"] == "running":
                return {"accepted": False, "response": "A browser automation is already running.", **self.state()}

        if decision.requires_confirmation:
            guarded = guard_action(
                permission_action,
                f"continue browser workflow: {command}",
                lambda: self._enqueue_command(command),
            )
            self._log(guarded, "warning" if guarded.startswith("Confirmation required") else "info")
            return {"accepted": False, "response": guarded, **self.state()}

        self._enqueue_command(command)
        return {"accepted": True, "response": f"Browser task started: {command}", **self.state()}

    def stop(self) -> dict:
        self._stop_requested = True
        self._paused = False
        self._log("Stop requested.", "warning")
        with self._lock:
            self._state["status"] = "stopping"
            self._state["currentAction"] = "Stopping automation"
        return self.state()

    def close(self) -> dict:
        self._stop_requested = True
        self._paused = False
        try:
            if self._context:
                self._context.close()
            if self._browser:
                self._browser.close()
            if self._playwright:
                self._playwright.stop()
        except Exception as error:
            self._log(f"Browser close warning: {error}", "warning")
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._set_status("idle", "Browser closed")
        self._log("Browser closed.", "success")
        return self.state()

    def pause(self) -> dict:
        self._paused = True
        self._log("Automation paused.", "warning")
        with self._lock:
            self._state["status"] = "paused"
            self._state["currentAction"] = "Paused"
        return self.state()

    def resume(self) -> dict:
        self._paused = False
        self._log("Automation resumed.", "info")
        with self._lock:
            self._state["status"] = "running"
            self._state["currentAction"] = "Resuming"
        return self.state()

    def screenshot_path(self) -> Path:
        return SCREENSHOT_PATH

    def _enqueue_command(self, command: str) -> str:
        with self._lock:
            self._stop_requested = False
            self._paused = False
            self._state["status"] = "running"
            self._state["currentAction"] = f"Queued: {command}"

        self._queue.put(command)
        if not self._worker or not self._worker.is_alive():
            self._worker = threading.Thread(target=self._worker_loop, daemon=True)
            self._worker.start()
        return f"Browser task started: {command}"

    def _worker_loop(self) -> None:
        while True:
            try:
                command = self._queue.get(timeout=1.0)
            except queue.Empty:
                with self._lock:
                    if self._state["status"] not in {"running", "paused", "stopping"}:
                        return
                continue

            self._run_command(command)
            self._queue.task_done()

    def _run_command(self, command: str) -> None:
        try:
            self._log(f"Task received: {command}", "info")
            self._ensure_browser()
            lowered = command.lower()

            youtube_query = self._extract_youtube_query(command)
            google_query = self._extract_google_query(command)
            open_target = self._extract_open_target(command)

            if youtube_query:
                self._youtube_search(youtube_query)
                response = f"YouTube search complete: {youtube_query}"
            elif google_query:
                self._google_search(google_query)
                response = f"Google search complete: {google_query}"
            elif open_target:
                self._open_website(open_target)
                response = f"Opened {open_target}"
            elif "summarize" in lowered or "summary" in lowered:
                response = self._summarize_page()
            else:
                response = self._general_navigation(command)

            self._record_history(command, response)
            self._set_status("idle", response)
            self._log(response, "success")
        except Exception as error:
            message = f"Browser automation failed: {error}"
            self._set_status("error", message)
            self._log(message, "error")

    def _ensure_browser(self) -> None:
        if self._page:
            return

        try:
            from playwright.sync_api import sync_playwright
        except ImportError as error:
            raise RuntimeError(
                "Playwright is not installed. Run: backend\\.venv\\Scripts\\python.exe -m pip install playwright"
            ) from error

        self._set_status("running", "Starting visible browser")
        self._playwright = sync_playwright().start()
        launch_args = {"headless": False, "slow_mo": 140}
        last_error = None
        for channel in ("chrome", "msedge", None):
            try:
                if channel:
                    self._browser = self._playwright.chromium.launch(channel=channel, **launch_args)
                else:
                    self._browser = self._playwright.chromium.launch(**launch_args)
                break
            except Exception as error:
                last_error = error

        if not self._browser:
            raise RuntimeError(
                "Could not launch a visible Chromium browser. Install Chrome/Edge or run: playwright install chromium"
            ) from last_error

        self._context = self._browser.new_context(viewport={"width": 1366, "height": 820}, accept_downloads=False)
        self._page = self._context.new_page()
        self._log("Visible browser opened.", "success")
        self._refresh_page_state()

    def _google_search(self, query: str) -> None:
        self._navigate("https://www.google.com")
        self._type_into_first(["textarea[name='q']", "input[name='q']", "[aria-label='Search']"], query)
        self._press("Enter")
        self._wait_load()
        self._refresh_page_state()
        self._log("Reading Google results.", "info")

    def _youtube_search(self, query: str) -> None:
        self._navigate("https://www.youtube.com")
        self._type_into_first(["input[name='search_query']", "input#search", "input[placeholder*='Search']"], query)
        self._press("Enter")
        self._wait_load()
        self._refresh_page_state()
        self._log("YouTube results displayed.", "success")

    def _open_website(self, target: str) -> None:
        url = self._normalize_url(target)
        self._navigate(url)
        self._refresh_page_state()

    def _general_navigation(self, command: str) -> str:
        if "scroll" in command.lower():
            self._set_status("running", "Scrolling page")
            self._page.mouse.wheel(0, 820)
            self._sleep(0.5)
            self._refresh_page_state()
            return "Scrolled the current page."

        match = re.search(r"\bclick\s+(.+)$", command, re.IGNORECASE)
        if match:
            label = match.group(1).strip(" .")
            self._click_by_text(label)
            self._refresh_page_state()
            return f"Clicked {label}."

        return "I need a more specific browser command, like search Google for AI tools or click Sign in."

    def _summarize_page(self) -> str:
        self._refresh_page_state()
        if not self._page:
            return "No browser page is open."
        text = self._page.locator("body").inner_text(timeout=3000)[:1600]
        if not text.strip():
            return "The page did not expose readable text."
        lines = [line.strip() for line in text.splitlines() if len(line.strip()) > 20][:6]
        return "Page summary:\n" + "\n".join(f"- {line[:220]}" for line in lines)

    def _navigate(self, url: str) -> None:
        self._checkpoint()
        self._set_status("running", f"Navigating to {url}")
        self._page.goto(url, wait_until="domcontentloaded", timeout=45000)
        self._wait_load()
        self._log(f"Opened {url}", "success")

    def _type_into_first(self, selectors: list[str], value: str) -> None:
        self._checkpoint()
        for selector in selectors:
            locator = self._page.locator(selector).first
            try:
                locator.wait_for(state="visible", timeout=5000)
                self._set_status("running", f"Typing: {value}")
                locator.click()
                locator.fill("")
                locator.type(value, delay=35)
                self._log(f"Typed search query: {value}", "success")
                return
            except Exception:
                continue
        raise RuntimeError("Could not find a visible search/input field.")

    def _click_by_text(self, label: str) -> None:
        self._checkpoint()
        self._set_status("running", f"Clicking {label}")
        locators = [
            self._page.get_by_role("button", name=re.compile(re.escape(label), re.IGNORECASE)).first,
            self._page.get_by_role("link", name=re.compile(re.escape(label), re.IGNORECASE)).first,
            self._page.get_by_text(re.compile(re.escape(label), re.IGNORECASE)).first,
        ]
        for locator in locators:
            try:
                locator.wait_for(state="visible", timeout=2500)
                locator.click()
                self._wait_load()
                self._log(f"Clicked {label}", "success")
                return
            except Exception:
                continue
        raise RuntimeError(f"Could not find a clickable element named {label}.")

    def _press(self, key: str) -> None:
        self._checkpoint()
        self._set_status("running", f"Pressing {key}")
        self._page.keyboard.press(key)
        self._log(f"Pressed {key}", "success")

    def _wait_load(self) -> None:
        self._checkpoint()
        self._page.wait_for_load_state("domcontentloaded", timeout=20000)
        self._sleep(0.7)
        self._capture_screenshot()

    def _refresh_page_state(self) -> None:
        if not self._page:
            return
        summary = self._dom_summary()
        tabs = []
        if self._context:
            for index, page in enumerate(self._context.pages):
                tabs.append({"index": index + 1, "title": self._safe_title(page), "url": page.url})
        with self._lock:
            self._state.update(
                {
                    "currentUrl": self._page.url,
                    "title": self._safe_title(self._page),
                    "domSummary": summary,
                    "tabs": tabs,
                }
            )
        self._capture_screenshot()

    def _dom_summary(self) -> dict[str, list[str]]:
        try:
            return self._page.evaluate(
                """
                () => {
                  const visible = (el) => {
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    return rect.width > 2 && rect.height > 2 && style.visibility !== 'hidden' && style.display !== 'none';
                  };
                  const text = (el) => (el.innerText || el.value || el.getAttribute('aria-label') || el.placeholder || '').trim().replace(/\\s+/g, ' ').slice(0, 80);
                  return {
                    inputs: [...document.querySelectorAll('input, textarea, [contenteditable=true]')].filter(visible).slice(0, 10).map(text).filter(Boolean),
                    buttons: [...document.querySelectorAll('button, [role=button], input[type=submit]')].filter(visible).slice(0, 14).map(text).filter(Boolean),
                    links: [...document.querySelectorAll('a[href]')].filter(visible).slice(0, 14).map(text).filter(Boolean),
                  };
                }
                """
            )
        except Exception:
            return {"inputs": [], "buttons": [], "links": []}

    def _capture_screenshot(self) -> None:
        if not self._page:
            return
        RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
        try:
            self._page.screenshot(path=str(SCREENSHOT_PATH), full_page=False)
            token = str(int(time.time() * 1000))
            with self._lock:
                self._state["screenshotUrl"] = f"/api/browser/screenshot?ts={token}"
                self._state["screenshotToken"] = token
        except Exception as error:
            self._log(f"Screenshot failed: {error}", "error")

    def _checkpoint(self) -> None:
        if self._stop_requested:
            raise RuntimeError("Automation stopped by user.")
        while self._paused and not self._stop_requested:
            time.sleep(0.2)
        if self._stop_requested:
            raise RuntimeError("Automation stopped by user.")

    def _sleep(self, seconds: float) -> None:
        deadline = time.time() + seconds
        while time.time() < deadline:
            self._checkpoint()
            time.sleep(0.1)

    def _set_status(self, status: str, action: str) -> None:
        with self._lock:
            self._state["status"] = status
            self._state["currentAction"] = action

    def _log(self, message: str, level: str = "info") -> None:
        entry = {
            "id": f"browser-{len(self._logs) + 1}",
            "createdAt": datetime.now().isoformat(timespec="seconds"),
            "level": level,
            "message": message,
        }
        with self._lock:
            self._logs.append(entry)
        log_activity(message, level, "browser")
        record_action("browser", message, {"level": level})

    def _record_history(self, command: str, response: str) -> None:
        with self._lock:
            self._history.append(
                {
                    "id": f"history-{len(self._history) + 1}",
                    "createdAt": datetime.now().isoformat(timespec="seconds"),
                    "command": command,
                    "response": response,
                    "url": self._state.get("currentUrl", ""),
                }
            )
        remember_event("browser", command[:180], response, {"url": self._state.get("currentUrl", "")})

    def _safe_title(self, page) -> str:
        try:
            return page.title()
        except Exception:
            return "Untitled"

    def _extract_google_query(self, text: str) -> str | None:
        patterns = (
            r"\bsearch\s+google\s+for\s+(.+)$",
            r"\bgoogle\s+search\s+(.+)$",
            r"\bsearch\s+the\s+web\s+for\s+(.+)$",
        )
        return self._first_match(patterns, text)

    def _extract_youtube_query(self, text: str) -> str | None:
        patterns = (
            r"\bopen\s+youtube\s+and\s+search\s+(.+)$",
            r"\bsearch\s+youtube\s+for\s+(.+)$",
            r"\byoutube\s+search\s+(.+)$",
        )
        return self._first_match(patterns, text)

    def _extract_open_target(self, text: str) -> str | None:
        match = re.search(r"\b(?:open|go to|navigate to)\s+(.+)$", text, re.IGNORECASE)
        if not match:
            return None
        target = match.group(1).strip(" .")
        if target.lower().startswith(("youtube and search", "google and search")):
            return None
        return target

    def _first_match(self, patterns: tuple[str, ...], text: str) -> str | None:
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip(" .")
        return None

    def _normalize_url(self, target: str) -> str:
        aliases = {
            "google": "https://www.google.com",
            "youtube": "https://www.youtube.com",
            "github": "https://github.com",
            "stackoverflow": "https://stackoverflow.com",
            "stack overflow": "https://stackoverflow.com",
            "linkedin": "https://www.linkedin.com",
            "reddit": "https://www.reddit.com",
        }
        lowered = target.lower().strip()
        if lowered in aliases:
            return aliases[lowered]
        if lowered.startswith(("http://", "https://")):
            return target
        if "." in target and " " not in target:
            return f"https://{target}"
        return f"https://www.google.com/search?q={quote_plus(target)}"

    def _is_sensitive(self, text: str) -> bool:
        lowered = text.lower()
        sensitive_terms = (
            "payment",
            "pay ",
            "checkout",
            "bank",
            "password",
            "login",
            "sign in",
            "delete",
            "download",
            "account settings",
            "purchase",
            "buy ",
        )
        return any(term in lowered for term in sensitive_terms)

    def _permission_action(self, text: str) -> str:
        if self._is_sensitive(text):
            return "browser.sensitive"
        if self._extract_google_query(text) or self._extract_youtube_query(text):
            return "internet.search"
        if self._extract_open_target(text):
            return "browser.open"
        return "browser.automation"


browser_operator = BrowserOperator()
