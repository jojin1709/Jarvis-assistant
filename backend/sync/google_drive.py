from __future__ import annotations

from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sync.session_store import access_token, provider_config, provider_state, save_provider_config, save_provider_token


PROVIDER = "google_drive"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def auth_url(redirect_uri: str, client_id: str | None = None) -> dict:
    config = provider_config(PROVIDER)
    resolved_client_id = client_id or config.get("clientId", "")
    query = urlencode(
        {
            "client_id": resolved_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "access_type": "offline",
            "prompt": "consent",
        }
    )
    return {"provider": PROVIDER, "url": f"{AUTH_URL}?{query}", "configured": bool(resolved_client_id)}


def configure(client_id: str, client_secret: str, redirect_uri: str) -> dict:
    return save_provider_config(PROVIDER, {"clientId": client_id, "clientSecret": client_secret, "redirectUri": redirect_uri, "tokenUrl": TOKEN_URL})


def save_token(refresh_token: str, access_token: str = "", expires_at: str = "") -> dict:
    save_provider_token(PROVIDER, {"refreshToken": refresh_token, "accessToken": access_token, "expiresAt": expires_at})
    return provider_state(PROVIDER)


def status() -> dict:
    return provider_state(PROVIDER)


def upload_file(local_path: str, remote_path: str) -> dict:
    token = access_token(PROVIDER)
    if not token:
        return {"ok": False, "message": "Google Drive access token is not connected."}
    from pathlib import Path

    path = Path(local_path)
    boundary = "jarvis-sync-boundary"
    metadata = f'{{"name":"{remote_path.split("/")[-1]}","parents":[]}}'.encode("utf-8")
    body = (
        b"--" + boundary.encode() + b"\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n" + metadata
        + b"\r\n--" + boundary.encode() + b"\r\nContent-Type: application/octet-stream\r\n\r\n"
        + path.read_bytes()
        + b"\r\n--" + boundary.encode() + b"--"
    )
    request = Request(
        "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
        data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": f"multipart/related; boundary={boundary}"},
        method="POST",
    )
    with urlopen(request, timeout=45) as response:
        return {"ok": 200 <= response.status < 300, "status": response.status, "provider": PROVIDER, "remotePath": remote_path}
