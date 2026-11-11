"""Phase 1 security regression tests (access control, injection, XSS sinks)."""
import io

import pytest
from PIL import Image

import main
import gtoolbox.ai as gt_ai
import gtoolbox.dialogs as gt_dialogs
import gtoolbox.routers.ai as gt_routers_ai
import gtoolbox.security as gt_security


def _png_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (4, 4), (255, 0, 0)).save(buf, "PNG")
    return buf.getvalue()


# ── Access control ───────────────────────────────────────────────

def test_local_index_ok(local_client):
    assert local_client.get("/").status_code == 200


def test_remote_blocked_when_lan_disabled(remote_client):
    assert remote_client.get("/").status_code == 403


@pytest.mark.parametrize("host", ["evil.example", "evil.example:8000", "attacker.localhost.evil:8000"])
def test_dns_rebinding_host_rejected(local_client, host):
    assert local_client.get("/api/network-info", headers={"host": host}).status_code == 403


def test_cross_site_origin_rejected(local_client):
    r = local_client.post("/api/delete-ai-models", headers={"origin": "https://evil.example"})
    assert r.status_code == 403


def test_null_origin_rejected(local_client):
    r = local_client.post("/api/delete-ai-models", headers={"origin": "null"})
    assert r.status_code == 403


def test_sec_fetch_site_cross_site_rejected(local_client):
    r = local_client.get("/api/network-info", headers={"sec-fetch-site": "cross-site"})
    assert r.status_code == 403


def test_same_origin_allowed(local_client):
    r = local_client.get("/api/network-info", headers={"origin": main_origin()})
    assert r.status_code == 200


def main_origin():
    return "http://127.0.0.1:8000"


def test_no_cors_headers(local_client):
    r = local_client.options("/api/delete-ai-models", headers={
        "origin": "https://evil.example", "access-control-request-method": "POST"})
    assert "access-control-allow-origin" not in r.headers


def test_remote_requires_token(lan_enabled, remote_client):
    assert remote_client.get("/").status_code == 401
    assert remote_client.get("/", headers={"x-gtoolbox-token": "wrong"}).status_code == 401


def test_pairing_link_sets_cookie_and_strips_token(lan_enabled, remote_client):
    r = remote_client.get(f"/?token={gt_security.ACCESS_TOKEN}")
    assert r.status_code == 303
    assert r.headers["location"] == "/"
    assert gt_security.TOKEN_COOKIE in r.cookies
    assert "httponly" in r.headers["set-cookie"].lower()
    remote_client.cookies.set(gt_security.TOKEN_COOKIE, gt_security.ACCESS_TOKEN)
    assert remote_client.get("/").status_code == 200


@pytest.mark.parametrize("path", sorted(gt_security.LOOPBACK_ONLY_PATHS))
def test_host_only_endpoints_refuse_paired_devices(lan_enabled, remote_client, path):
    remote_client.cookies.set(gt_security.TOKEN_COOKIE, gt_security.ACCESS_TOKEN)
    assert remote_client.post(path).status_code == 403


def test_pairing_url_only_shown_to_host(lan_enabled, local_client, remote_client):
    assert "pairing_url" in local_client.get("/api/network-info").json()
    remote_client.cookies.set(gt_security.TOKEN_COOKIE, gt_security.ACCESS_TOKEN)
    assert "pairing_url" not in remote_client.get("/api/network-info").json()


# ── G1: save dialog command injection ───────────────────────────

def test_save_dialog_inputs_are_sanitized(local_client, monkeypatch):
    seen = {}

    def fake_dialog(name, ext):
        seen["name"], seen["ext"] = name, ext
        return "CANCELED"

    monkeypatch.setattr(gt_dialogs, "NATIVE_SAVE_DIALOG_HOOK", fake_dialog)
    payload = "x.a';Start-Process calc;'"
    r = local_client.post("/api/save-blob-file",
                          files={"file": ("f.bin", b"data")},
                          data={"suggested_filename": payload})
    assert r.json()["canceled"] is True
    assert seen["ext"] == ""          # non-alphanumeric extension dropped
    assert "/" not in seen["name"] and "\\" not in seen["name"]


@pytest.mark.parametrize("raw,expected", [
    ("../../etc/passwd", ("passwd", "")),
    ("photo.PNG", ("photo.PNG", "PNG")),
    ("a.b;c", ("a.b;c", "")),
])
def test_clean_dialog_inputs(raw, expected):
    from pathlib import Path
    name, ext = gt_dialogs._clean_dialog_inputs(raw, Path(raw).suffix)
    assert (name, ext) == expected


# ── G2: target_format path traversal ────────────────────────────

@pytest.mark.parametrize("fmt", ["png/../../PWNED", "..\\..\\x.png", "exe", "png\x00"])
def test_convert_rejects_unknown_formats(local_client, fmt):
    for ep in ("/convert", "/convert-universal"):
        r = local_client.post(ep, files={"file": ("a.png", _png_bytes(), "image/png")},
                              data={"target_format": fmt})
        assert r.status_code == 400, (ep, fmt)


def test_convert_still_works(local_client):
    r = local_client.post("/convert", files={"file": ("a.png", _png_bytes(), "image/png")},
                          data={"target_format": "JPG"})
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/jpeg"


# ── G6/G8: XSS sinks and information leaks ──────────────────────

def test_error_page_escapes_and_hides_traceback(local_client, monkeypatch):
    def boom():
        raise RuntimeError("<script>alert(1)</script>")
    monkeypatch.setattr(gt_routers_ai, "check_ai_models_status", boom)
    client = type(local_client)(main.app, base_url="http://127.0.0.1:8000",
                                client=("127.0.0.1", 1), raise_server_exceptions=False)
    r = client.get("/api/ai-status", headers={"accept": "text/html"})
    assert r.status_code == 500
    assert "<script>" not in r.text
    assert "Traceback" not in r.text


def test_ai_status_hides_paths(local_client):
    data = local_client.get("/api/ai-status").json()
    assert all("path" not in m for m in data["models"].values())


# ── G7: Whisper model whitelist ─────────────────────────────────

@pytest.mark.parametrize("name", ["../../etc", "someone/evil-model", "/tmp/model"])
def test_whisper_rejects_arbitrary_models(name):
    with pytest.raises(ValueError):
        gt_ai.get_whisper_model(name)
