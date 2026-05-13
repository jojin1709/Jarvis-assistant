import base64
import binascii
import ctypes
import json
import os
from ctypes import wintypes
from pathlib import Path


RUNTIME_DIR = Path(__file__).resolve().parents[1] / "runtime"
KEY_STORE_PATH = RUNTIME_DIR / "provider_keys.secure.json"


class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]


def save_secret(name: str, value: str) -> None:
    data = _load()
    if value:
        data[_clean(name)] = _protect(value)
    else:
        data.pop(_clean(name), None)
    _save(data)


def delete_secret(name: str) -> None:
    data = _load()
    data.pop(_clean(name), None)
    _save(data)


def get_secret(name: str) -> str:
    data = _load()
    protected = data.get(_clean(name))
    if not protected:
        return ""
    try:
        return _unprotect(protected)
    except (OSError, ValueError, TypeError, UnicodeDecodeError, binascii.Error):
        return ""


def has_secret(name: str) -> bool:
    return bool(get_secret(name))


def masked_secret(name: str) -> str:
    value = get_secret(name)
    if not value:
        return ""
    if len(value) <= 8:
        return "••••"
    return f"{value[:4]}••••{value[-4:]}"


def _protect(value: str) -> dict[str, str]:
    raw = value.encode("utf-8")
    if os.name == "nt":
        try:
            return {"scheme": "dpapi", "value": base64.b64encode(_crypt_protect(raw)).decode("ascii")}
        except Exception:
            pass
    return {"scheme": "local-b64", "value": base64.b64encode(raw).decode("ascii")}


def _unprotect(payload: dict[str, str]) -> str:
    if not isinstance(payload, dict):
        return ""
    scheme = payload.get("scheme")
    encoded = payload.get("value") or ""
    if not encoded:
        return ""
    raw = base64.b64decode(encoded.encode("ascii"))
    if scheme == "dpapi" and os.name == "nt":
        return _crypt_unprotect(raw).decode("utf-8")
    return raw.decode("utf-8")


def _crypt_protect(data: bytes) -> bytes:
    blob_in, _buffer = _blob_from_bytes(data)
    blob_out = DATA_BLOB()
    if not ctypes.windll.crypt32.CryptProtectData(ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)):
        raise ctypes.WinError()
    try:
        return ctypes.string_at(blob_out.pbData, blob_out.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)


def _crypt_unprotect(data: bytes) -> bytes:
    blob_in, _buffer = _blob_from_bytes(data)
    blob_out = DATA_BLOB()
    if not ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)):
        raise ctypes.WinError()
    try:
        return ctypes.string_at(blob_out.pbData, blob_out.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)


def _blob_from_bytes(data: bytes) -> tuple[DATA_BLOB, ctypes.Array]:
    buffer = ctypes.create_string_buffer(data)
    return DATA_BLOB(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char))), buffer


def _load() -> dict:
    if not KEY_STORE_PATH.exists():
        return {}
    try:
        data = json.loads(KEY_STORE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _save(data: dict) -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    KEY_STORE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _clean(name: str) -> str:
    return name.strip().lower().replace(" ", "_")
