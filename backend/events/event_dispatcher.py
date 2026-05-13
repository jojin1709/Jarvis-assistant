from __future__ import annotations

from events.event_bus import emit_event
from events.event_handlers import install_default_handlers


_INSTALLED = False


def dispatch(kind: str, payload: dict | None = None, level: str = "info") -> dict:
    global _INSTALLED
    if not _INSTALLED:
        install_default_handlers()
        _INSTALLED = True
    return emit_event(kind, payload, level)
