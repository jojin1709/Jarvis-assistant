import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent

load_dotenv(PROJECT_DIR / ".env")
load_dotenv(BACKEND_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    voice_name: str = os.getenv("JX_JARVIS_VOICE", "en-US-GuyNeural")
    owner_name: str = os.getenv("JX_JARVIS_OWNER_NAME", "Jojin")
    backend_port: int = int(os.getenv("JX_JARVIS_BACKEND_PORT", "8765"))
    speech_dir: Path = BACKEND_DIR / "runtime" / "speech"
    uploads_dir: Path = BACKEND_DIR / "runtime" / "uploads"
    system_tasks_enabled: bool = os.getenv("JX_JARVIS_ENABLE_SYSTEM_TASKS", "true").lower() == "true"


settings = Settings()
settings.speech_dir.mkdir(parents=True, exist_ok=True)
settings.uploads_dir.mkdir(parents=True, exist_ok=True)
