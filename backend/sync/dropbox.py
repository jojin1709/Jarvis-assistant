from __future__ import annotations

from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sync.session_store import access_token, provider_config, provider_state, save_provider_config, save_provider_token


PROVIDER = "dropbox"
AUTH_URL = "https://www.dropbox.com/oauth2/authorize"
TOKEN_URL = "https://api.dropboxapi.com/oauth2/token"


def auth_url(redirect_uri: str, client_id: str | None = None) -> dict:
    config = provider_config(PROVIDER)
    resolved_client_id = client_id or config.get("clientId", "")
    query = urlencode({"client_id": resolved_client_id, "redirect_uri": redirect_uri, "response_type": "code", "token_access_type": "offline"})
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
        return {"ok": False, "message": "Dropbox access token is not connected."}
    import json
    from pathlib import Path

    request = Request(
        "https://content.dropboxapi.com/2/files/upload",
        data=Path(local_path).read_bytes(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/octet-stream",
            "Dropbox-API-Arg": json.dumps({"path": f"/Jarvis/{remote_path}", "mode": "overwrite", "autorename": False}),
        },
        method="POST",
    )
    with urlopen(request, timeout=45) as response:
        return {"ok": 200 <= response.status < 300, "status": response.status, "provider": PROVIDER, "remotePath": remote_path}
