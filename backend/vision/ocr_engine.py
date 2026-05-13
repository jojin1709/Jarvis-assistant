from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class OCRResult:
    ok: bool
    text: str = ""
    words: list[dict] | None = None
    engine: str = "pytesseract"
    error: str = ""

    def as_dict(self) -> dict:
        return {
            "ok": self.ok,
            "text": self.text,
            "words": self.words or [],
            "engine": self.engine,
            "error": self.error,
        }


def extract_text(image_or_path, timeout: int = 5) -> OCRResult:
    try:
        from PIL import Image, ImageOps
        import pytesseract

        image = Image.open(image_or_path) if isinstance(image_or_path, (str, Path)) else image_or_path
        prepared = ImageOps.grayscale(image)
        text = " ".join(pytesseract.image_to_string(prepared, timeout=timeout).split())[:4000]
        words = []
        try:
            data = pytesseract.image_to_data(prepared, output_type=pytesseract.Output.DICT, timeout=timeout)
            for index, raw_text in enumerate(data.get("text", [])):
                value = str(raw_text or "").strip()
                if not value:
                    continue
                confidence = float(data.get("conf", ["-1"])[index])
                if confidence < 35:
                    continue
                words.append(
                    {
                        "text": value,
                        "confidence": round(confidence, 1),
                        "x": int(data["left"][index]),
                        "y": int(data["top"][index]),
                        "width": int(data["width"][index]),
                        "height": int(data["height"][index]),
                    }
                )
        except Exception:
            words = []
        return OCRResult(ok=True, text=text, words=words)
    except Exception as error:
        return OCRResult(ok=False, error=str(error))
