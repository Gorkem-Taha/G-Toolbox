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
