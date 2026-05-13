from __future__ import annotations

from api.browser_automation import browser_operator
from api.memory_storage import memory_storage_state, recent_memories
from context.browser_context import browser_context
from context.desktop_context import desktop_context
from context.environment_analyzer import environment_snapshot
from context.session_state import session_state
from context.terminal_context import terminal_context
from desktop.automation import desktop_automation
from providers.provider_router import browser_provider_status
from scheduler.task_scheduler import scheduler
from terminal.service import terminal_service


def build_world_state(include_vision: bool = False) -> dict:
    vision = None
    if include_vision:
        try:
            from vision.screenshot import capture_screen

            vision = capture_screen()
        except Exception as error:
            vision = {"ok": False, "error": str(error)}
    return {
        "environment": environment_snapshot(),
        "session": session_state(),
        "browser": browser_operator.state(),
        "browserContext": browser_context(),
        "terminal": {"jobs": terminal_service.history(limit=16)},
        "terminalContext": terminal_context(limit=16),
        "memory": memory_storage_state(),
        "recentMemory": recent_memories(limit=8),
        "desktop": desktop_automation.status(),
        "desktopContext": desktop_context(),
        "providers": browser_provider_status(),
        "scheduler": scheduler.list(),
        "vision": vision,
    }
