from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from itertools import count

from providers.secure_store import get_secret, save_secret


MASTER_KEY_NAME = "cloud_sync_master_key"


def encrypt_bytes(data: bytes) -> bytes:
    key = _master_key()
    nonce = os.urandom(16)
    ciphertext = _xor_stream(data, key, nonce)
    tag = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()
    envelope = {
        "scheme": "jarvis-sync-sha256-stream-v1",
        "nonce": base64.b64encode(nonce).decode("ascii"),
        "tag": base64.b64encode(tag).decode("ascii"),
        "payload": base64.b64encode(ciphertext).decode("ascii"),
    }
    return json.dumps(envelope, separators=(",", ":")).encode("utf-8")


def decrypt_bytes(envelope_bytes: bytes) -> bytes:
    envelope = json.loads(envelope_bytes.decode("utf-8"))
    if envelope.get("scheme") != "jarvis-sync-sha256-stream-v1":
        raise ValueError("Unsupported sync encryption scheme.")
    key = _master_key()
    nonce = base64.b64decode(envelope["nonce"])
    ciphertext = base64.b64decode(envelope["payload"])
    expected = base64.b64decode(envelope["tag"])
    actual = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(actual, expected):
        raise ValueError("Encrypted sync bundle failed integrity verification.")
    return _xor_stream(ciphertext, key, nonce)


def encryption_status() -> dict:
    return {"enabled": True, "scheme": "jarvis-sync-sha256-stream-v1", "keyStored": bool(get_secret(MASTER_KEY_NAME))}


def _master_key() -> bytes:
    secret = get_secret(MASTER_KEY_NAME)
    if not secret:
        secret = base64.b64encode(os.urandom(32)).decode("ascii")
        save_secret(MASTER_KEY_NAME, secret)
    return base64.b64decode(secret.encode("ascii"))


def _xor_stream(data: bytes, key: bytes, nonce: bytes) -> bytes:
    output = bytearray()
    for block_index in count():
        if len(output) >= len(data):
            break
        block = hashlib.sha256(key + nonce + block_index.to_bytes(8, "big")).digest()
        output.extend(block)
    stream = bytes(output[: len(data)])
    return bytes(left ^ right for left, right in zip(data, stream))
