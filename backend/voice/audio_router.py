from __future__ import annotations

import os


def play_activation_sound() -> dict:
    if os.name == "nt":
        try:
            import winsound

            winsound.MessageBeep(winsound.MB_OK)
            return {"ok": True, "backend": "winsound"}
        except Exception as error:
            return {"ok": False, "error": str(error)}
    print("\a", end="", flush=True)
    return {"ok": True, "backend": "terminal-bell"}


def play_error_sound() -> dict:
    if os.name == "nt":
        try:
            import winsound

            winsound.MessageBeep(winsound.MB_ICONHAND)
            return {"ok": True, "backend": "winsound"}
        except Exception as error:
            return {"ok": False, "error": str(error)}
    print("\a", end="", flush=True)
    return {"ok": True, "backend": "terminal-bell"}
