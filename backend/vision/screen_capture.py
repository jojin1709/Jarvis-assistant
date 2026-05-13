from __future__ import annotations

from datetime import datetime
from pathlib import Path

from api.browser_automation import browser_operator


RUNTIME_DIR = Path(__file__).resolve().parents[1] / "runtime" / "vision"
SCREENSHOT_PATH = RUNTIME_DIR / "screen.png"


def capture_screen(path: str | Path | None = None) -> dict:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    output = Path(path or SCREENSHOT_PATH)
    try:
        from PIL import ImageGrab

        image = ImageGrab.grab()
        image.save(output)
        return {"ok": True, "source": "desktop", "path": str(output), "capturedAt": _now(), "width": image.width, "height": image.height}
    except Exception as error:
        browser_path = browser_operator.screenshot_path()
        if browser_path.exists():
            return {
                "ok": True,
                "source": "browser",
                "path": str(browser_path),
                "capturedAt": _now(),
                "note": f"Desktop capture unavailable: {error}",
            }
        return {"ok": False, "error": f"Screen capture failed: {error}", "capturedAt": _now()}


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")
