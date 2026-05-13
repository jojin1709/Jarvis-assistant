from __future__ import annotations

from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sync.session_store import access_token, provider_config, provider_state, save_provider_config, save_provider_token


PROVIDER = "onedrive"
AUTH_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
SCOPES = ["offline_access", "Files.ReadWrite.AppFolder"]


def auth_url(redirect_uri: str, client_id: str | None = None) -> dict:
    config = provider_config(PROVIDER)
    resolved_client_id = client_id or config.get("clientId", "")
    query = urlencode({"client_id": resolved_client_id, "redirect_uri": redirect_uri, "response_type": "code", "scope": " ".join(SCOPES)})
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
        return {"ok": False, "message": "OneDrive access token is not connected."}
    from pathlib import Path

    safe_remote = remote_path.strip("/").replace("\\", "/")
    request = Request(
        f"https://graph.microsoft.com/v1.0/me/drive/special/approot:/{safe_remote}:/content",
        data=Path(local_path).read_bytes(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/octet-stream"},
        method="PUT",
    )
    with urlopen(request, timeout=45) as response:
        return {"ok": 200 <= response.status < 300, "status": response.status, "provider": PROVIDER, "remotePath": remote_path}
