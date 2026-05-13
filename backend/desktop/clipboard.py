from __future__ import annotations


def read_clipboard() -> dict:
    try:
        import pyperclip

        return {"ok": True, "text": pyperclip.paste()}
    except Exception as error:
        return {"ok": False, "error": str(error), "text": ""}


def write_clipboard(text: str) -> dict:
    try:
        import pyperclip

        pyperclip.copy(text)
        return {"ok": True, "message": "Clipboard updated."}
    except Exception as error:
        return {"ok": False, "error": str(error)}
