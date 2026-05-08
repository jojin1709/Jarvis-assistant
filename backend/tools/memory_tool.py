from api.memory import handle_memory_command, profile_summary
from app.config import settings


def run_memory_command(text: str) -> str | None:
    return handle_memory_command(text)


def memory_profile() -> dict[str, object]:
    return profile_summary(settings.owner_name)
