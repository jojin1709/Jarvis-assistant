import re

from api.ai_provider import chat_ai_messages
from app.config import settings


MALAYALAM_RE = re.compile(r"[\u0D00-\u0D7F]")


def detect_language(text: str) -> str:
    return "ml" if MALAYALAM_RE.search(text or "") else "en"


def normalize_language_mode(value: object) -> str:
    mode = str(value or "auto").strip().lower()
    if mode in {"en", "english"}:
        return "en"
    if mode in {"ml", "malayalam"}:
        return "ml"
    return "auto"


def resolve_language(text: str, language_mode: object = "auto") -> str:
    mode = normalize_language_mode(language_mode)
    if mode in {"en", "ml"}:
        return mode
    return detect_language(text)


def language_name(language: str) -> str:
    return "Malayalam" if language == "ml" else "English"


def command_language_instruction(language: str) -> str:
    if language == "ml":
        return (
            "The user spoke Malayalam. Reply in natural Malayalam, but keep app names, file paths, "
            "commands, and code-related terms readable."
        )
    return "Reply in English."


def normalize_command_to_english(text: str, language: str) -> str:
    if language != "ml" or not _has_ai_key():
        return _fallback_malayalam_command(text) if language == "ml" else text

    try:
        translated = chat_ai_messages(
            temperature=0,
            max_tokens=180,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Translate the user's Malayalam command into one short English command for a desktop assistant. "
                        "Preserve app names, filenames, folder names, and programming language names. "
                        "Return only the translated command, no explanation."
                    ),
                },
                {"role": "user", "content": text},
            ],
        )
        translated = translated.strip().strip('"')
        return translated or _fallback_malayalam_command(text)
    except Exception:
        return _fallback_malayalam_command(text)


def localize_response(text: str, language: str) -> str:
    if language != "ml" or not text.strip():
        return text

    if not _has_ai_key():
        return text

    try:
        translated = chat_ai_messages(
            temperature=0.2,
            max_tokens=450,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Translate this assistant response into natural Malayalam. "
                        "Keep file paths, URLs, app names, confirmation tokens, code identifiers, and English commands unchanged. "
                        "Keep it concise. Return only the translated response."
                    ),
                },
                {"role": "user", "content": text},
            ],
        )
        return translated.strip() or text
    except Exception:
        return text


def _has_ai_key() -> bool:
    provider = settings.ai_provider
    if provider == "sarvam":
        return bool(settings.sarvam_api_key)
    if provider == "deepseek":
        return bool(settings.deepseek_api_key)
    if provider == "nvidia":
        return bool(settings.nvidia_api_key)
    if provider == "auto":
        return bool(settings.sarvam_api_key or settings.deepseek_api_key or settings.nvidia_api_key or settings.groq_api_key)
    return bool(settings.groq_api_key)


def _fallback_malayalam_command(text: str) -> str:
    normalized = " ".join(text.lower().strip().split())
    for wake in ("ഹേ ജാർവിസ്", "ഹായ് ജാർവിസ്", "ജാർവിസ്", "ജാര്‍വിസ്"):
        normalized = normalized.replace(wake, "").strip(" ,:.-")

    replacements = {
        "യൂട്യൂബ്": "youtube",
        "ഗൂഗിൾ": "google",
        "ക്രോം": "chrome",
        "കാൽക്കുലേറ്റർ": "calculator",
        "നോട്ട്പാഡ്": "notepad",
        "വി എസ് കോഡ്": "vs code",
        "വിഎസ് കോഡ്": "vs code",
        "സമയം": "time",
        "തീയതി": "date",
        "ഫോൾഡർ": "folder",
        "ഫയൽ": "file",
        "കോഡ്": "code",
        "വെബ്സൈറ്റ്": "website",
        "ഗെയിം": "game",
        "ഓപ്പൺ": "open",
        "തുറക്കൂ": "open",
        "തുറക്ക്": "open",
        "ഉണ്ടാക്കൂ": "create",
        "നിർമ്മിക്കൂ": "create",
        "എഴുതൂ": "write",
        "ഓർമ്മിക്കൂ": "remember",
    }
    for source, target in replacements.items():
        normalized = normalized.replace(source, target)

    has_open = "open" in normalized
    if has_open:
        for app in ("youtube", "google", "chrome", "calculator", "notepad", "vs code"):
            if app in normalized:
                return f"open {app}"

    if "time" in normalized:
        return "what time is it"
    if "date" in normalized:
        return "what date is it"
    if "remember" in normalized:
        return normalized
    if "code" in normalized or "website" in normalized or "game" in normalized:
        return normalized

    return normalized
