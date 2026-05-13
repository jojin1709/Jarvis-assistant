import base64
from datetime import datetime
from pathlib import Path

from api.browser_automation import browser_operator
from api.memory_storage import remember_event
from vision.screenshot_analyzer import analyze_screenshot, capture_and_analyze


RUNTIME_DIR = Path(__file__).resolve().parents[1] / "runtime" / "vision"
SCREENSHOT_PATH = RUNTIME_DIR / "screen.png"


def capture_screen() -> dict:
    return capture_and_analyze()


def analyze_image(path: str | Path | None = None, source: str = "image", note: str = "") -> dict:
    delegated = analyze_screenshot(path or SCREENSHOT_PATH, source=source, note=note)
    if delegated.get("ok"):
        return delegated

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
        detected_text = _ocr_text(image)
        regions = _region_summary(image)
        browser_context = _browser_context() if source == "browser" else {}
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
            "detectedText": detected_text,
            "screenRegions": regions,
            "browserContext": browser_context,
            "note": note,
            "imageBase64": encoded,
            "summary": _summary(source, image.width, image.height, brightness, dominant, note, detected_text, regions, browser_context),
        }
        try:
            remember_event("cache", "Screenshot analyzed", result["summary"], {"path": str(image_path), "source": source})
        except OSError:
            pass
        return result
    except Exception as error:
        return {"ok": False, "error": f"Image analysis failed: {error}"}


def _ocr_text(image) -> str:
    try:
        from PIL import ImageOps
        import pytesseract

        prepared = ImageOps.grayscale(image)
        text = pytesseract.image_to_string(prepared, timeout=5)
        return " ".join(text.split())[:1600]
    except Exception:
        return ""


def _region_summary(image) -> list[dict[str, object]]:
    from PIL import ImageStat

    width, height = image.size
    regions = [
        ("top-left", (0, 0, width // 2, height // 2)),
        ("top-right", (width // 2, 0, width, height // 2)),
        ("bottom-left", (0, height // 2, width // 2, height)),
        ("bottom-right", (width // 2, height // 2, width, height)),
    ]
    result = []
    for name, box in regions:
        crop = image.crop(box)
        stat = ImageStat.Stat(crop)
        brightness = round(sum(stat.mean) / 3, 1)
        dominant = "#%02x%02x%02x" % crop.resize((1, 1)).getpixel((0, 0))
        result.append({"name": name, "brightness": brightness, "dominantColor": dominant})
    return result


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


def _summary(
    source: str,
    width: int,
    height: int,
    brightness: float,
    dominant: str,
    note: str,
    detected_text: str = "",
    regions: list[dict[str, object]] | None = None,
    browser_context: dict | None = None,
) -> str:
    visibility = "bright" if brightness > 180 else "dim" if brightness < 75 else "balanced"
    extra = f" {note}" if note else ""
    text_part = f" OCR detected readable text: {detected_text[:180]}." if detected_text else ""
    browser_part = ""
    if browser_context and browser_context.get("url"):
        browser_part = f" Browser page: {browser_context.get('title') or 'Untitled'} at {browser_context.get('url')}."
    region_part = ""
    if regions:
        brightest = max(regions, key=lambda item: float(item.get("brightness") or 0))
        region_part = f" Brightest region: {brightest.get('name')}."
    return (
        f"Analyzed {source} screenshot ({width}x{height}). "
        f"The frame is {visibility}; dominant color {dominant}.{region_part}{text_part}{browser_part}{extra}"
    )
