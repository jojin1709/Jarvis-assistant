import mimetypes
from pathlib import Path

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from api.ai_provider import ask_ai
from api.memory_storage import remember_event
from api.permissions import evaluate_permission, log_activity
from api.sarvam_services import analyze_sarvam_document
from app.config import settings


TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".log",
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".html",
    ".css",
    ".xml",
    ".yml",
    ".yaml",
}
DOCUMENT_INTELLIGENCE_EXTENSIONS = {".pdf"}


def _read_text(path: Path) -> str:
    raw = path.read_bytes()[:12000]
    return raw.decode("utf-8", errors="replace")


def save_and_analyze(file: FileStorage) -> dict[str, str | int | bool | None]:
    filename = secure_filename(file.filename or "uploaded-file")
    if not filename:
        filename = "uploaded-file"

    output_path = settings.uploads_dir / filename
    counter = 1
    while output_path.exists():
        output_path = settings.uploads_dir / f"{output_path.stem}-{counter}{output_path.suffix}"
        counter += 1

    decision = evaluate_permission("file.create", f"save uploaded file {output_path.name}", path=output_path)
    if not decision.allowed:
        log_activity(f"Denied upload {output_path.name}: {decision.message}", "error", "security")
        return {
            "filename": filename,
            "path": None,
            "size": 0,
            "mime_type": None,
            "text_indexed": False,
            "document_intelligence_used": False,
            "document_output": None,
            "summary": decision.message,
        }

    file.save(output_path)
    size = output_path.stat().st_size
    mime_type = mimetypes.guess_type(output_path.name)[0] or "application/octet-stream"
    extension = output_path.suffix.lower()
    text_indexed = extension in TEXT_EXTENSIONS
    document_output = None
    document_intelligence_used = False
    preview_text = ""

    if _should_use_document_intelligence(extension):
        document_intelligence_used = True
        try:
            document_result = analyze_sarvam_document(output_path)
            document_output = document_result.get("output_zip")
            extracted_text = str(document_result.get("extracted_text") or "")
            if document_result.get("success") and extracted_text:
                prompt = (
                    "Summarize this Sarvam document intelligence extraction for JX JARVIS. "
                    "Give a concise useful summary, important details, and suggested next actions.\n\n"
                    f"File name: {output_path.name}\n"
                    f"Extracted content:\n{extracted_text[:12000]}"
                )
                summary = ask_ai(prompt)
            else:
                summary = str(document_result.get("summary") or "Sarvam document intelligence completed.")
        except Exception as error:
            summary = (
                f"File received and stored: {output_path.name}. Sarvam document intelligence failed: {error}"
            )
    elif text_indexed:
        content = _read_text(output_path)
        preview_text = content[:3000]
        prompt = (
            "Analyze this uploaded file for JX JARVIS. Give a concise useful summary, "
            "important details, and suggested next actions.\n\n"
            f"File name: {output_path.name}\n"
            f"Content:\n{content}"
        )
        summary = ask_ai(prompt)
    elif mime_type.startswith("image/"):
        try:
            from vision.screenshot import analyze_image

            analysis = analyze_image(output_path, source="uploaded image")
            summary = analysis.get("summary") or f"Image received and stored: {output_path.name}."
            if analysis.get("detectedText"):
                summary = f"{summary}\nDetected text: {analysis['detectedText'][:600]}"
        except Exception as error:
            summary = f"Image received and stored: {output_path.name}. Local image analysis failed: {error}"
    else:
        summary = (
            f"File received and stored: {output_path.name}. Type detected: {mime_type}. "
            "For binary media such as images and videos, I can track the file and use its metadata. "
            "Text extraction is available for text, code, markdown, CSV, and JSON files."
        )

    try:
        remember_event(
            "cache",
            f"Uploaded file: {output_path.name}",
            summary,
            {
                "path": str(output_path),
                "mime_type": mime_type,
                "size": size,
                "text_indexed": text_indexed,
                "document_intelligence_used": document_intelligence_used,
                "preview": preview_text[:1200],
            },
        )
    except OSError:
        pass

    return {
        "filename": output_path.name,
        "path": str(output_path),
        "size": size,
        "mime_type": mime_type,
        "text_indexed": text_indexed,
        "document_intelligence_used": document_intelligence_used,
        "document_output": document_output,
        "preview": preview_text,
        "summary": summary,
    }


def _should_use_document_intelligence(extension: str) -> bool:
    provider = settings.document_intelligence_provider
    if provider == "off":
        return False
    if provider == "sarvam":
        return bool(settings.sarvam_api_key) and extension in DOCUMENT_INTELLIGENCE_EXTENSIONS
    if provider == "auto":
        return bool(settings.sarvam_api_key) and extension in DOCUMENT_INTELLIGENCE_EXTENSIONS
    return False
