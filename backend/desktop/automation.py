from __future__ import annotations

import time
from dataclasses import dataclass

from api.permissions import evaluate_permission, log_activity


@dataclass
class DesktopActionResult:
    ok: bool
    action: str
    message: str
    data: dict | None = None

    def as_dict(self) -> dict:
        return {"ok": self.ok, "action": self.action, "message": self.message, "data": self.data or {}}


class DesktopAutomation:
    def status(self) -> dict:
        available = _pyautogui_available()
        return {"available": available, "backend": "pyautogui", "message": "ready" if available else "pyautogui is not installed"}

    def move_mouse(self, x: int, y: int, duration: float = 0.1) -> DesktopActionResult:
        decision = evaluate_permission("automation.run", f"move mouse to {x},{y}")
        if not decision.allowed or decision.requires_confirmation:
            return DesktopActionResult(False, "mouse.move", decision.message)
        try:
            import pyautogui

            pyautogui.moveTo(int(x), int(y), duration=max(0, float(duration)))
            log_activity(f"Mouse moved to {x},{y}", "success", "desktop")
            return DesktopActionResult(True, "mouse.move", f"Mouse moved to {x},{y}")
        except Exception as error:
            return DesktopActionResult(False, "mouse.move", str(error))

    def click(self, x: int | None = None, y: int | None = None) -> DesktopActionResult:
        decision = evaluate_permission("automation.run", "desktop click")
        if not decision.allowed or decision.requires_confirmation:
            return DesktopActionResult(False, "mouse.click", decision.message)
        try:
            import pyautogui

            if x is None or y is None:
                pyautogui.click()
            else:
                pyautogui.click(int(x), int(y))
            log_activity("Desktop click executed", "success", "desktop")
            return DesktopActionResult(True, "mouse.click", "Click executed")
        except Exception as error:
            return DesktopActionResult(False, "mouse.click", str(error))

    def type_text(self, text: str, interval: float = 0.01) -> DesktopActionResult:
        decision = evaluate_permission("automation.run", "type text through desktop automation")
        if not decision.allowed or decision.requires_confirmation:
            return DesktopActionResult(False, "keyboard.type", decision.message)
        try:
            import pyautogui

            pyautogui.write(text, interval=max(0, float(interval)))
            return DesktopActionResult(True, "keyboard.type", f"Typed {len(text)} character(s)")
        except Exception as error:
            return DesktopActionResult(False, "keyboard.type", str(error))

    def hotkey(self, keys: list[str]) -> DesktopActionResult:
        decision = evaluate_permission("automation.run", f"press hotkey {'+'.join(keys)}")
        if not decision.allowed or decision.requires_confirmation:
            return DesktopActionResult(False, "keyboard.hotkey", decision.message)
        try:
            import pyautogui

            pyautogui.hotkey(*keys)
            time.sleep(0.1)
            return DesktopActionResult(True, "keyboard.hotkey", f"Pressed {'+'.join(keys)}")
        except Exception as error:
            return DesktopActionResult(False, "keyboard.hotkey", str(error))


def _pyautogui_available() -> bool:
    try:
        import pyautogui  # noqa: F401

        return True
    except Exception:
        return False


desktop_automation = DesktopAutomation()
