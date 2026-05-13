from __future__ import annotations

from pathlib import Path


ACTION_WORDS = {
    "ok",
    "cancel",
    "submit",
    "send",
    "save",
    "open",
    "close",
    "next",
    "back",
    "login",
    "sign",
    "continue",
    "retry",
    "run",
    "build",
}

INPUT_WORDS = {"search", "email", "password", "name", "prompt", "message", "type", "enter"}
POPUP_WORDS = {"error", "warning", "failed", "exception", "confirm", "permission", "blocked", "required"}


def detect_ui(image_or_path, ocr_words: list[dict] | None = None) -> dict:
    from PIL import Image, ImageStat

    image = Image.open(image_or_path).convert("RGB") if isinstance(image_or_path, (str, Path)) else image_or_path.convert("RGB")
    words = ocr_words or []
    elements = []
    popups = []

    for word in words:
        text = str(word.get("text") or "").strip()
        lowered = text.lower()
        box = _box(word)
        if lowered in ACTION_WORDS:
            elements.append({"type": "button_or_action", "label": text, "bounds": box, "confidence": word.get("confidence", 65)})
        elif lowered in INPUT_WORDS:
            elements.append({"type": "input_hint", "label": text, "bounds": box, "confidence": word.get("confidence", 60)})
        if lowered in POPUP_WORDS:
            popups.append({"label": text, "bounds": box, "severity": "high" if lowered in {"error", "failed", "blocked"} else "medium"})

    regions = _regions(image)
    center = image.crop((image.width // 5, image.height // 5, image.width * 4 // 5, image.height * 4 // 5))
    center_brightness = round(sum(ImageStat.Stat(center).mean) / 3, 1)
    outer_brightness = round(sum(region["brightness"] for region in regions) / len(regions), 1)
    modal_likely = abs(center_brightness - outer_brightness) > 35 and bool(popups or elements)

    return {
        "elements": elements[:80],
        "popups": popups[:20],
        "regions": regions,
        "modalLikely": modal_likely,
        "elementCount": len(elements),
    }


def _box(word: dict) -> dict:
    return {
        "x": int(word.get("x") or 0),
        "y": int(word.get("y") or 0),
        "width": int(word.get("width") or 0),
        "height": int(word.get("height") or 0),
    }


def _regions(image) -> list[dict]:
    from PIL import ImageStat

    width, height = image.size
    specs = [
        ("top-left", (0, 0, width // 2, height // 2)),
        ("top-right", (width // 2, 0, width, height // 2)),
        ("bottom-left", (0, height // 2, width // 2, height)),
        ("bottom-right", (width // 2, height // 2, width, height)),
        ("center", (width // 4, height // 4, width * 3 // 4, height * 3 // 4)),
    ]
    result = []
    for name, box in specs:
        crop = image.crop(box)
        stat = ImageStat.Stat(crop)
        brightness = round(sum(stat.mean) / 3, 1)
        dominant = "#%02x%02x%02x" % crop.resize((1, 1)).getpixel((0, 0))
        result.append({"name": name, "brightness": brightness, "dominantColor": dominant})
    return result
