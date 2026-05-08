import base64
from datetime import datetime
from pathlib import Path

from api.browser_automation import browser_operator
from api.memory_storage import remember_event


RUNTIME_DIR = Path(__file__).resolve().parents[1] / "runtime" / "vision"
SCREENSHOT_PATH = RUNTIME_DIR / "screen.png"


def capture_screen() -> dict:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    try:
        from PIL import ImageGrab

        image = ImageGrab.grab()
        image.save(SCREENSHOT_PATH)
        return analyze_image(SCREENSHOT_PATH, source="desktop")
    except Exception as error:
        browser_path = browser_operator.screenshot_path()
        if browser_path.exists():
            return analyze_image(browser_path, source="browser", note=f"Desktop capture failed: {error}")
        return {"ok": False, "error": f"Screenshot capture failed: {error}"}


def analyze_image(path: str | Path | None = None, source: str = "image", note: str = "") -> dict:
    image_path = Path(path or SCREENSHOT_PATH)
    if not image_path.exists():
        return {"ok": False, "error": "No screenshot is available to analyze."}

    try:
        from PIL import Image, ImageStat

        image = Image.open(image_path).convert("RGB")
        stat = ImageStat.Stat(image)
        avg = tuple(round(value, 1) for value in stat.mean)
        brightness = round(sum(stat.mean) / 3, 1)
        thumbnail = image.resize((1, 1))
        dominant = "#%02x%02x%02x" % thumbnail.getpixel((0, 0))
        encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
        result = {
            "ok": True,
            "source": source,
            "path": str(image_path),
            "capturedAt": datetime.now().isoformat(timespec="seconds"),
            "width": image.width,
            "height": image.height,
            "brightness": brightness,
            "averageColor": avg,
            "dominantColor": dominant,
            "note": note,
            "imageBase64": encoded,
            "summary": _summary(source, image.width, image.height, brightness, dominant, note),
        }
        try:
            remember_event("cache", "Screenshot analyzed", result["summary"], {"path": str(image_path), "source": source})
        except OSError:
            pass
        return result
    except Exception as error:
        return {"ok": False, "error": f"Image analysis failed: {error}"}


def _summary(source: str, width: int, height: int, brightness: float, dominant: str, note: str) -> str:
    visibility = "bright" if brightness > 180 else "dim" if brightness < 75 else "balanced"
    extra = f" {note}" if note else ""
    return f"Analyzed {source} screenshot ({width}x{height}). The frame is {visibility}; dominant color {dominant}.{extra}"
