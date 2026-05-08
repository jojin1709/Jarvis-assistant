import base64
import json
import zipfile
from pathlib import Path
from typing import Any

from app.config import settings


def _client():
    if not settings.sarvam_api_key:
        raise RuntimeError("SARVAM_API_KEY is not configured.")

    try:
        from sarvamai import SarvamAI
    except ImportError as error:
        raise RuntimeError("Install the sarvamai package with pip install -r backend/requirements.txt.") from error

    return SarvamAI(api_subscription_key=settings.sarvam_api_key)


def _value(data: Any, key: str, default: Any = None) -> Any:
    if isinstance(data, dict):
        return data.get(key, default)
    return getattr(data, key, default)


def _language_code(language: str) -> str:
    configured = settings.sarvam_tts_language_code.strip()
    if configured and configured.lower() != "auto":
        return configured
    return "ml-IN" if language == "ml" else "en-IN"


def synthesize_sarvam_speech(text: str, language: str, output_path: Path) -> Path:
    client = _client()
    request = {
        "model": settings.sarvam_tts_model,
        "text": text,
        "target_language_code": _language_code(language),
        "speaker": settings.sarvam_tts_speaker,
        "speech_sample_rate": settings.sarvam_tts_sample_rate,
        "output_audio_codec": "wav",
    }
    try:
        response = client.text_to_speech.convert(**request)
    except TypeError:
        request.pop("speech_sample_rate", None)
        request.pop("output_audio_codec", None)
        response = client.text_to_speech.convert(**request)

    audios = _value(response, "audios", [])
    if not audios:
        raise RuntimeError("Sarvam text-to-speech returned no audio.")

    output_path.write_bytes(base64.b64decode("".join(audios)))
    return output_path


def transcribe_sarvam_audio(audio_path: Path) -> str:
    client = _client()
    with audio_path.open("rb") as audio_file:
        response = client.speech_to_text.transcribe(
            file=audio_file,
            model=settings.sarvam_stt_model,
            mode=settings.sarvam_stt_mode,
        )

    transcript = str(_value(response, "transcript", "") or "").strip()
    if not transcript:
        raise RuntimeError("Sarvam speech-to-text returned an empty transcript.")
    return transcript


def analyze_sarvam_document(document_path: Path) -> dict[str, str | bool | None]:
    client = _client()
    job = client.document_intelligence.create_job(
        language=settings.sarvam_doc_language,
        output_format=settings.sarvam_doc_output_format,
    )
    job.upload_file(str(document_path))
    job.start()
    status = job.wait_until_complete()

    job_state = str(_value(status, "job_state", "") or "")
    if job_state.lower() not in {"completed", "complete", "succeeded", "success"}:
        return {
            "success": False,
            "summary": f"Sarvam document intelligence did not complete. Job state: {job_state or status}",
            "output_zip": None,
            "extracted_text": "",
        }

    output_zip = document_path.with_name(f"{document_path.stem}-sarvam-output.zip")
    job.download_output(str(output_zip))

    extracted_text = _extract_zip_text(output_zip)
    summary = (
        f"Sarvam document intelligence completed. Output saved to {output_zip.name}."
        if not extracted_text
        else f"Sarvam document intelligence completed. Extracted preview:\n\n{extracted_text[:2400]}"
    )

    return {
        "success": True,
        "summary": summary,
        "output_zip": str(output_zip),
        "extracted_text": extracted_text,
    }


def _extract_zip_text(zip_path: Path) -> str:
    snippets: list[str] = []
    with zipfile.ZipFile(zip_path) as archive:
        for name in archive.namelist():
            suffix = Path(name).suffix.lower()
            if suffix not in {".md", ".txt", ".html", ".json"}:
                continue

            raw = archive.read(name)[:20000]
            text = raw.decode("utf-8", errors="replace")
            if suffix == ".json":
                text = _json_preview(text)
            snippets.append(f"--- {name} ---\n{text.strip()}")

            if sum(len(snippet) for snippet in snippets) > 12000:
                break

    return "\n\n".join(snippets).strip()


def _json_preview(text: str) -> str:
    try:
        return json.dumps(json.loads(text), ensure_ascii=False, indent=2)[:8000]
    except json.JSONDecodeError:
        return text
