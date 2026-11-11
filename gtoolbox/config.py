"""Paths, settings and constants shared by every G-Toolbox module."""

import json
import logging
import os
import socket
import sys
from pathlib import Path

from fastapi.templating import Jinja2Templates


# Set global socket default timeout to 180s to prevent premature read timeouts on slow networks
socket.setdefaulttimeout(180)


if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
    RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", BASE_DIR))
else:
    BASE_DIR = Path(__file__).resolve().parent.parent  # project root (gtoolbox/..)
    RESOURCE_DIR = BASE_DIR


# Writable state (temp files, settings, pairing token, model weights). Defaults to
# the program folder (portable Windows layout); read-only installs such as the
# Linux AppImage point GTOOLBOX_DATA_DIR at a per-user folder instead.
DATA_DIR = Path(os.environ["GTOOLBOX_DATA_DIR"]).expanduser() if os.environ.get("GTOOLBOX_DATA_DIR") else BASE_DIR


DATA_DIR.mkdir(parents=True, exist_ok=True)


# Extra, user-writable site-packages for on-demand AI libraries when the bundled
# Python is read-only (AppImage). pip installs there with --target.
PIP_TARGET = os.environ.get("GTOOLBOX_PIP_TARGET")


if PIP_TARGET:
    Path(PIP_TARGET).mkdir(parents=True, exist_ok=True)
    if PIP_TARGET not in sys.path:
        sys.path.insert(0, PIP_TARGET)


UPLOAD_DIR = DATA_DIR / "uploads"
DOWNLOAD_DIR = DATA_DIR / "downloads"
UPLOAD_DIR.mkdir(exist_ok=True)
DOWNLOAD_DIR.mkdir(exist_ok=True)


try:
    import certifi
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
except ImportError:
    pass


logger = logging.getLogger("uvicorn.error")
SETTINGS_PATH = DATA_DIR / "gtoolbox_settings.json"
TOKEN_PATH = DATA_DIR / ".gtoolbox_token"


def load_settings() -> dict:
    try:
        return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_settings(settings: dict) -> None:
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2), encoding="utf-8")


def lan_access_enabled() -> bool:
    """LAN access is enabled by --lan, GTOOLBOX_LAN=1 or the saved setting."""
    if "--lan" in sys.argv:
        return True
    if os.environ.get("GTOOLBOX_LAN", "").strip().lower() in ("1", "true", "yes"):
        return True
    return bool(load_settings().get("lan_access", False))


STATIC_DIR = None


for s_cand in [RESOURCE_DIR / "static", BASE_DIR / "static", Path.cwd() / "static"]:
    if s_cand.exists():
        STATIC_DIR = s_cand
        break


if STATIC_DIR is None:
    STATIC_DIR = BASE_DIR / "static"
    STATIC_DIR.mkdir(parents=True, exist_ok=True)


TEMPLATES_DIR = None


for t_cand in [RESOURCE_DIR / "templates", BASE_DIR / "templates", Path.cwd() / "templates"]:
    if t_cand.exists():
        TEMPLATES_DIR = t_cand
        break


if TEMPLATES_DIR is None:
    TEMPLATES_DIR = BASE_DIR / "templates"
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)


templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# ── Desteklenen formatlar ─────────────────────────────────────────
IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "bmp", "gif", "tiff", "ico"}


VIDEO_EXTENSIONS = {"mp4", "avi", "mkv", "mov", "webm", "flv", "wmv"}
AUDIO_EXTENSIONS = {"mp3", "wav", "ogg", "flac", "aac", "m4a", "wma"}
ALL_TARGET_FORMATS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS | AUDIO_EXTENSIONS
MIME_MAP = {
    # Resim
    "image/png": "image", "image/jpeg": "image", "image/webp": "image",
    "image/bmp": "image", "image/gif": "image", "image/tiff": "image",
    "image/x-icon": "image",
    # Video
    "video/mp4": "video", "video/x-msvideo": "video", "video/x-matroska": "video",
    "video/quicktime": "video", "video/webm": "video", "video/x-flv": "video",
    "video/x-ms-wmv": "video",
    "audio/mpeg": "audio", "audio/wav": "audio", "audio/ogg": "audio",
    "audio/flac": "audio", "audio/aac": "audio", "audio/mp4": "audio",
    "audio/x-m4a": "audio", "audio/x-ms-wma": "audio",
}
from . import __version__

APP_VERSION = __version__  # single source: gtoolbox/__init__.py
GITHUB_REPO = "Gorkem-Taha/G-Toolbox"
