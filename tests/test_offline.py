"""Phase 4a/4b: the UI must not depend on any remote host."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_no_remote_assets_in_ui():
    for rel in ("templates/index.html", "static/css/style.css", "static/vendor/fonts/fonts.css"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert not re.search(r"(src|href)=\"https?://|@import url\('https?://|url\(https?://", text), rel


def test_vendored_assets_exist(local_client):
    html = local_client.get("/").text
    for href in re.findall(r'(?:href|src)="(/static/[^"]+)"', html):
        assert local_client.get(href).status_code == 200, href
    css = (ROOT / "static/vendor/fontawesome/css/all.min.css").read_text(encoding="utf-8")
    for font in set(re.findall(r"\.\./webfonts/([\w.-]+)", css)):
        assert (ROOT / "static/vendor/fontawesome/webfonts" / font).exists(), font


def test_service_worker_served_from_root(local_client):
    r = local_client.get("/sw.js")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/javascript")
    assert "register('/sw.js')" in local_client.get("/").text
    for asset in re.findall(r"'(/static/[^']+)'", r.text):
        assert local_client.get(asset).status_code == 200, asset


def test_data_dir_separates_writable_state():
    import os
    import main
    data = os.environ["GTOOLBOX_DATA_DIR"]
    for path in (main.UPLOAD_DIR, main.DOWNLOAD_DIR, main.SETTINGS_PATH, main.TOKEN_PATH):
        assert str(path).startswith(data), path
    assert str(main.MODEL_REGISTRY["RealESRGAN_x4plus.pth"][1]).startswith(data)


def test_pip_installs_into_target_when_set(monkeypatch, tmp_path):
    import main
    seen = {}

    class P:
        returncode = 0

        def communicate(self, timeout=None):
            return "", ""

    monkeypatch.setattr(main, "PIP_TARGET", str(tmp_path))
    monkeypatch.setattr(main.subprocess, "Popen", lambda cmd, **kw: seen.setdefault("cmd", cmd) and P())
    main._run_pip_step(["install", "rembg"], "x", 1)
    assert seen["cmd"][seen["cmd"].index("--target") + 1] == str(tmp_path)


def test_update_refused_on_read_only_install(local_client, monkeypatch):
    import main
    monkeypatch.setattr(main.os, "access", lambda p, m: False)
    r = local_client.post("/apply-update")
    assert r.status_code == 409
