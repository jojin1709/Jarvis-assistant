import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent

load_dotenv(PROJECT_DIR / ".env")
load_dotenv(BACKEND_DIR / ".env")


def default_owner_name() -> str:
    for key in ("JX_JARVIS_OWNER_NAME", "USERNAME", "USER"):
        value = os.getenv(key, "").strip()
        if value:
            return value
    return "User"


@dataclass(frozen=True)
class Settings:
    ai_provider: str = os.getenv("JX_JARVIS_AI_PROVIDER", "groq").strip().lower()
    tts_provider: str = os.getenv("JX_JARVIS_TTS_PROVIDER", "edge").strip().lower()
    stt_provider: str = os.getenv("JX_JARVIS_STT_PROVIDER", "google").strip().lower()
    document_intelligence_provider: str = os.getenv("JX_JARVIS_DOCUMENT_INTELLIGENCE_PROVIDER", "off").strip().lower()
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    claude_model: str = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-latest")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_model: str = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    deepseek_thinking: str = os.getenv("DEEPSEEK_THINKING", "disabled").strip().lower()
    nvidia_api_key: str = os.getenv("NVIDIA_API_KEY", "")
    nvidia_model: str = os.getenv("NVIDIA_MODEL", "deepseek-ai/deepseek-v4-pro")
    nvidia_base_url: str = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    nvidia_top_p: float = float(os.getenv("NVIDIA_TOP_P", "0.95"))
    nvidia_thinking: bool = os.getenv("NVIDIA_THINKING", "false").strip().lower() == "true"
    sarvam_api_key: str = os.getenv("SARVAM_API_KEY", "")
    sarvam_model: str = os.getenv("SARVAM_MODEL", "sarvam-30b")
    sarvam_base_url: str = os.getenv("SARVAM_BASE_URL", "https://api.sarvam.ai")
    sarvam_tts_model: str = os.getenv("SARVAM_TTS_MODEL", "bulbul:v3")
    sarvam_tts_language_code: str = os.getenv("SARVAM_TTS_LANGUAGE_CODE", "auto")
    sarvam_tts_speaker: str = os.getenv("SARVAM_TTS_SPEAKER", "shubh")
    sarvam_tts_sample_rate: int = int(os.getenv("SARVAM_TTS_SAMPLE_RATE", "24000"))
    sarvam_stt_model: str = os.getenv("SARVAM_STT_MODEL", "saaras:v3")
    sarvam_stt_mode: str = os.getenv("SARVAM_STT_MODE", "transcribe")
    sarvam_doc_language: str = os.getenv("SARVAM_DOC_LANGUAGE", "en-IN")
    sarvam_doc_output_format: str = os.getenv("SARVAM_DOC_OUTPUT_FORMAT", "md")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.1")
    local_llamacpp_base_url: str = os.getenv("LOCAL_LLAMACPP_BASE_URL", "http://127.0.0.1:8080/v1")
    local_llamacpp_model: str = os.getenv("LOCAL_LLAMACPP_MODEL", "local-model")
    voice_name: str = os.getenv("JX_JARVIS_VOICE", "en-US-GuyNeural")
    malayalam_voice_name: str = os.getenv("JX_JARVIS_MALAYALAM_VOICE", "ml-IN-MidhunNeural")
    speech_languages: tuple[str, ...] = tuple(
        language.strip()
        for language in os.getenv("JX_JARVIS_SPEECH_LANGUAGES", "en-IN,ml-IN").split(",")
        if language.strip()
    )
    owner_name: str = default_owner_name()
    backend_port: int = int(os.getenv("JX_JARVIS_BACKEND_PORT", "8765"))
    speech_dir: Path = BACKEND_DIR / "runtime" / "speech"
    uploads_dir: Path = BACKEND_DIR / "runtime" / "uploads"
    system_tasks_enabled: bool = os.getenv("JX_JARVIS_ENABLE_SYSTEM_TASKS", "true").lower() == "true"


settings = Settings()
settings.speech_dir.mkdir(parents=True, exist_ok=True)
settings.uploads_dir.mkdir(parents=True, exist_ok=True)
