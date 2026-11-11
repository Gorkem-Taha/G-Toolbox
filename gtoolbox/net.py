"""HTTPS downloads with verification always on; hashing; Authenticode checks."""

import os
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

from .config import logger


def _tls_context() -> ssl.SSLContext:
    """Verified TLS context. Uses certifi's CA bundle when available (fresh Windows
    installs often lack intermediate CAs), otherwise the system store."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _safe_urlopen(req: urllib.request.Request, timeout: int = 180):
    """Opens a URL with certificate verification always on (never falls back to unverified)."""
    try:
        return urllib.request.urlopen(req, timeout=timeout, context=_tls_context())
    except Exception as e:
        if "CERTIFICATE_VERIFY_FAILED" in str(e):
            raise RuntimeError(
                "TLS certificate verification failed. Check the system date/time, antivirus HTTPS "
                "scanning or a proxy intercepting the connection, then try again."
            ) from e
        raise


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_authenticode_microsoft(exe_path: Path) -> bool:
    """Windows only: True if exe_path has a valid Authenticode signature by Microsoft."""
    if sys.platform != "win32":
        return False
    ps = (
        "$s = Get-AuthenticodeSignature -LiteralPath $env:GT_VERIFY_PATH; "
        "if ($s.Status -eq 'Valid' -and $s.SignerCertificate.Subject -match 'O=Microsoft Corporation') "
        "{ 'OK' } else { 'BAD:' + $s.Status }"
    )
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
            capture_output=True, text=True, timeout=60,
            env=dict(os.environ, GT_VERIFY_PATH=str(exe_path)),
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return res.stdout.strip() == "OK"
    except Exception as e:
        logger.warning(f"Signature verification failed to run: {e}")
        return False
