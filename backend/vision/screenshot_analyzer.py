from __future__ import annotations

import base64
from datetime import datetime
from pathlib import Path

from api.browser_automation import browser_operator
from api.memory_storage import remember_event
from vision.ocr_engine import extract_text
from vision.screen_capture import capture_screen as capture_screen_file
from vision.ui_detector import detect_ui
from vision.visual_reasoner import reason_about_screen


def capture_and_analyze() -> dict:
    capture = capture_screen_file()
    if not capture.get("ok"):
        return capture
    return analyze_screenshot(capture["path"], source=capture.get("source", "desktop"), note=capture.get("note", ""))


def analyze_screenshot(path: str | Path, source: str = "image", note: str = "") -> dict:
    image_path = Path(path)
    if not image_path.exists():
        return {"ok": False, "error": "Screenshot does not exist."}
    try:
        from PIL import Image, ImageStat

        image = Image.open(image_path).convert("RGB")
        stat = ImageStat.Stat(image)
        avg = tuple(round(value, 1) for value in stat.mean)
        brightness = round(sum(stat.mean) / 3, 1)
        dominant = "#%02x%02x%02x" % image.resize((1, 1)).getpixel((0, 0))
        ocr = extract_text(image).as_dict()
        ui = detect_ui(image, ocr.get("words") or [])
        browser_context = _browser_context() if source == "browser" else {}
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
            "ocr": ocr,
            "detectedText": ocr.get("text", ""),
            "ui": ui,
            "screenRegions": ui.get("regions", []),
            "browserContext": browser_context,
            "note": note,
            "imageBase64": base64.b64encode(image_path.read_bytes()).decode("ascii"),
        }
        result["reasoning"] = reason_about_screen(result)
        result["summary"] = result["reasoning"]["summary"]
        try:
            remember_event("cache", "Screenshot analyzed", result["summary"], {"path": str(image_path), "source": source})
        except OSError:
            pass
        return result
    except Exception as error:
        return {"ok": False, "error": f"Screenshot analysis failed: {error}"}


def _browser_context() -> dict:
    try:
        state = browser_operator.state()
        return {
            "title": state.get("title", ""),
            "url": state.get("currentUrl", ""),
            "domSummary": state.get("domSummary", {}),
        }
    except Exception:
        return {}
