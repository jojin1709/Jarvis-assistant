import mimetypes
from pathlib import Path

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from api.groq_ai import ask_groq
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

    file.save(output_path)
    size = output_path.stat().st_size
    mime_type = mimetypes.guess_type(output_path.name)[0] or "application/octet-stream"
    extension = output_path.suffix.lower()
    text_indexed = extension in TEXT_EXTENSIONS

    if text_indexed:
        content = _read_text(output_path)
        prompt = (
            "Analyze this uploaded file for JX JARVIS. Give a concise useful summary, "
            "important details, and suggested next actions.\n\n"
            f"File name: {output_path.name}\n"
            f"Content:\n{content}"
        )
        summary = ask_groq(prompt)
    else:
        summary = (
            f"File received and stored: {output_path.name}. Type detected: {mime_type}. "
            "For binary media such as images and videos, I can track the file and use its metadata. "
            "Text extraction is available for text, code, markdown, CSV, and JSON files."
        )

    return {
        "filename": output_path.name,
        "path": str(output_path),
        "size": size,
        "mime_type": mime_type,
        "text_indexed": text_indexed,
        "summary": summary,
    }
