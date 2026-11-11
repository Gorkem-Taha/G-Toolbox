"""Signed in-app updates (ed25519-signed SHA256SUMS of GitHub releases)."""

import json
import os
import re
import shutil
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from .config import APP_VERSION, BASE_DIR, GITHUB_REPO
from .files import _path_inside
from .net import _safe_urlopen, sha256_file


UPDATE_PUBLIC_KEY_B64 = "6Bz9iNc1LkjIO28rz7iiwsS2PhV7mzO+x49VUHL+fAw="
UPDATE_ALLOWED_EXTS = {".py", ".html", ".js", ".css", ".json", ".png", ".ico", ".txt", ".md"}
UPDATE_PROTECTED = {"venv", "runtime", "uploads", "downloads", ".git", ".env"}


def _version_tuple(v: str) -> tuple:
    nums = re.findall(r"\d+", str(v))
    return tuple(int(n) for n in nums[:3]) + (0,) * (3 - len(nums[:3]))


def _http_get(url: str, accept: str = "application/octet-stream", timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": f"G-Toolbox/{APP_VERSION}", "Accept": accept})
    with _safe_urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _latest_release() -> dict:
    data = _http_get(f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest",
                     accept="application/vnd.github+json")
    return json.loads(data)


def verify_release_manifest(sums: bytes, signature: bytes) -> dict:
    """Verifies SHA256SUMS against the embedded ed25519 key; returns {filename: sha256}."""
    import base64
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    pub = Ed25519PublicKey.from_public_bytes(base64.b64decode(UPDATE_PUBLIC_KEY_B64))
    # Raw 64-byte signature, or a base64-encoded one (never strip raw bytes).
    sig = signature if len(signature) == 64 else base64.b64decode(signature.strip())
    try:
        pub.verify(sig, sums)
    except InvalidSignature:
        raise RuntimeError("Update signature is invalid. The release was not signed by the G-Toolbox key.")
    manifest = {}
    for line in sums.decode("utf-8").splitlines():
        parts = line.strip().split()
        if len(parts) == 2 and re.fullmatch(r"[0-9a-fA-F]{64}", parts[0]):
            manifest[parts[1].lstrip("*")] = parts[0].lower()
    return manifest


def safe_extract_zip(zip_path: Path, dest: Path) -> None:
    """Extracts a zip, refusing absolute paths and '..' entries (zip-slip)."""
    dest = dest.resolve()
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.infolist():
            target = (dest / member.filename).resolve()
            if not _path_inside(target, dest):
                raise RuntimeError(f"Unsafe path in update archive: {member.filename}")
        zf.extractall(dest)


def check_for_update() -> dict:
    rel = _latest_release()
    latest = str(rel.get("tag_name", "")).lstrip("v")
    return {
        "status": "ok",
        "current": APP_VERSION,
        "latest": latest,
        "update_available": _version_tuple(latest) > _version_tuple(APP_VERSION),
    }


def install_is_writable() -> bool:
    return os.access(BASE_DIR, os.W_OK)


def apply_latest_update(work: Path, progress=lambda pct, msg: None) -> dict:
    """Downloads, verifies and installs the latest signed release. Raises on failure."""
    rel = _latest_release()
    latest = str(rel.get("tag_name", "")).lstrip("v")
    if _version_tuple(latest) <= _version_tuple(APP_VERSION):
        return {"status": "up_to_date", "current": APP_VERSION, "latest": latest,
                "message": f"G-Toolbox is up to date ({APP_VERSION})."}

    assets = {a.get("name"): a.get("browser_download_url") for a in rel.get("assets", [])}
    if "SHA256SUMS" not in assets or "SHA256SUMS.sig" not in assets:
        raise RuntimeError("Release has no signed checksum manifest; refusing to update.")

    progress(25, "Verifying release signature...")
    manifest = verify_release_manifest(_http_get(assets["SHA256SUMS"]), _http_get(assets["SHA256SUMS.sig"]))
    zip_name = next((n for n in manifest if n.endswith("-Windows.zip") and n in assets), None)
    if not zip_name:
        raise RuntimeError("Signed manifest does not list an application zip.")

    progress(40, f"Downloading {zip_name}...")
    work.mkdir(parents=True, exist_ok=True)
    zip_path = work / "update.zip"
    zip_path.write_bytes(_http_get(assets[zip_name], timeout=300))
    if sha256_file(zip_path) != manifest[zip_name]:
        raise RuntimeError("Downloaded update does not match the signed checksum.")

    progress(70, "Applying update...")
    extract_path = work / "x"
    safe_extract_zip(zip_path, extract_path)
    items = list(extract_path.iterdir())
    root_dir = items[0] if len(items) == 1 and items[0].is_dir() else extract_path
    copied = 0
    for item in root_dir.rglob("*"):
        if not item.is_file():
            continue
        rel_path = item.relative_to(root_dir)
        if any(part in UPDATE_PROTECTED for part in rel_path.parts):
            continue
        if item.suffix.lower() in UPDATE_ALLOWED_EXTS:
            target = BASE_DIR / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)
            copied += 1
    return {"status": "success", "current": APP_VERSION, "latest": latest, "files": copied,
            "message": f"G-Toolbox updated to {latest}. Please restart the application."}
