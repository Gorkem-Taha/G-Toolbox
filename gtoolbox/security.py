"""Access control: loopback/LAN policy, pairing token, cross-site and DNS-rebinding guards."""

import hmac
import html
import ipaddress
import os
import secrets
from typing import Optional

from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from .config import TOKEN_PATH, lan_access_enabled, logger


TOKEN_COOKIE = "gt_token"


# Endpoints that touch the host desktop, install software or delete data:
# never reachable from another device, even with a valid token.
LOOPBACK_ONLY_PATHS = {
    "/api/save-task-file",
    "/api/save-blob-file",
    "/api/restart-as-admin",
    "/api/open-security-settings",
    "/apply-update",
    "/api/install-ai-models",
    "/api/delete-ai-models",
    "/update-ytdlp",
    "/api/lan-access",
}


def _load_or_create_token() -> str:
    try:
        tok = TOKEN_PATH.read_text(encoding="utf-8").strip()
        if len(tok) >= 20:
            return tok
    except Exception:
        pass
    tok = secrets.token_urlsafe(24)
    try:
        TOKEN_PATH.write_text(tok, encoding="utf-8")
        os.chmod(TOKEN_PATH, 0o600)
    except Exception as e:
        logger.warning(f"Could not persist pairing token: {e}")
    return tok


ACCESS_TOKEN = _load_or_create_token()


def rotate_access_token() -> str:
    """Replaces the pairing token; every paired device must pair again."""
    global ACCESS_TOKEN
    try:
        TOKEN_PATH.unlink()
    except FileNotFoundError:
        pass
    ACCESS_TOKEN = _load_or_create_token()
    return ACCESS_TOKEN


def _is_loopback(host: str) -> bool:
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _host_header_allowed(host_header: str) -> bool:
    if not host_header:
        return False
    if host_header.startswith("["):  # [::1]:8000
        hostname = host_header[1:].split("]", 1)[0]
    else:
        hostname = host_header.rsplit(":", 1)[0] if host_header.count(":") == 1 else host_header
    if hostname.lower() == "localhost":
        return True
    try:
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        return False


def _token_valid(candidate: Optional[str]) -> bool:
    return bool(candidate) and hmac.compare_digest(candidate, ACCESS_TOKEN)


def _deny(status: int, message: str, request: Request):
    if "text/html" in request.headers.get("accept", ""):
        return HTMLResponse(
            status_code=status,
            content=(
                "<!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'>"
                "<title>G-Toolbox</title></head><body style='font-family:sans-serif;background:#0d1117;color:#c9d1d9;padding:30px;'>"
                f"<h2>G-Toolbox</h2><p>{html.escape(message)}</p></body></html>"
            ),
        )
    return JSONResponse(status_code=status, content={"success": False, "message": message})


async def access_guard(request: Request, call_next):
    client_host = request.client.host if request.client else ""
    is_local = _is_loopback(client_host)
    host_header = request.headers.get("host", "")

    if not _host_header_allowed(host_header):
        return _deny(403, "Invalid Host header.", request)

    origin = request.headers.get("origin")
    if request.headers.get("sec-fetch-site") == "cross-site" or (
        origin is not None and origin != f"{request.url.scheme}://{host_header}"
    ):
        return _deny(403, "Cross-site requests are not allowed.", request)

    if not is_local:
        if not lan_access_enabled():
            return _deny(403, "LAN access is disabled on this G-Toolbox instance.", request)
        if request.url.path in LOOPBACK_ONLY_PATHS:
            return _deny(403, "This action is only available on the host computer.", request)

        query_token = request.query_params.get("token")
        if request.method == "GET" and _token_valid(query_token):
            # Pairing link: store the token in a cookie and drop it from the URL.
            resp = RedirectResponse(url=request.url.path or "/", status_code=303)
            resp.set_cookie(
                TOKEN_COOKIE, ACCESS_TOKEN, max_age=365 * 24 * 3600,
                httponly=True, samesite="strict", path="/",
            )
            return resp

        presented = request.cookies.get(TOKEN_COOKIE) or request.headers.get("x-gtoolbox-token")
        if not _token_valid(presented):
            return _deny(
                401,
                "Pairing required. Open G-Toolbox on your computer, go to the device mode "
                "window and open the pairing link shown there on this device.",
                request,
            )

    return await call_next(request)


def get_lan_ip() -> str:
    """Detects the primary LAN IPv4 address of the host machine."""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
