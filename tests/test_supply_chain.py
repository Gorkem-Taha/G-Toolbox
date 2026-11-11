"""Phase 2 supply-chain tests: TLS, pinned hashes, signed updates."""
import base64
import io
import ssl
import urllib.request
import zipfile
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import main
import gtoolbox.ai as gt_ai
import gtoolbox.config as gt_config
import gtoolbox.downloads as gt_downloads
import gtoolbox.net as gt_net
import gtoolbox.updates as gt_updates


# ── TLS ───────────────────────────────────────────────────────────

def test_safe_urlopen_never_falls_back_to_unverified(monkeypatch):
    calls = []

    def fake_urlopen(req, timeout=None, context=None):
        calls.append(context)
        raise urllib.error.URLError(ssl.SSLCertVerificationError("CERTIFICATE_VERIFY_FAILED"))

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(RuntimeError, match="TLS certificate verification failed"):
        gt_net._safe_urlopen(urllib.request.Request("https://example.invalid"))
    assert len(calls) == 1
    assert calls[0].verify_mode == ssl.CERT_REQUIRED
    assert calls[0].check_hostname is True


def test_ytdlp_keeps_certificate_checks():
    opts = gt_downloads._build_ytdlp_opts()
    assert not opts.get("nocheckcertificate")
    assert not opts.get("legacy_server_connect")


def test_pip_does_not_trust_hosts(monkeypatch):
    seen = {}

    class FakeProc:
        returncode = 0

        def communicate(self, timeout=None):
            return "", ""

    def fake_popen(cmd, **kw):
        seen["cmd"] = cmd
        return FakeProc()

    monkeypatch.setattr(gt_ai.subprocess, "Popen", fake_popen)
    gt_ai._run_pip_step(["install", "x"], "x", 1)
    assert "--trusted-host" not in seen["cmd"]


def test_launcher_has_no_tls_or_defender_bypass():
    src = (Path(main.__file__).parent / "launcher.cs").read_text(encoding="utf-8")
    for needle in ("ServerCertificateValidationCallback", "--trusted-host", "Add-MpPreference",
                   "Zone.Identifier", "get-pip.py\""):
        assert needle not in src, needle
    assert "RequireSha256(zipPath, SecurityHelper.PythonEmbedSha256)" in src
    assert "IsSignedByMicrosoft(vcRedistPath)" in src


# ── Model integrity ──────────────────────────────────────────────

def test_all_models_have_pinned_hashes():
    assert set(gt_ai.MODEL_SHA256) == set(gt_ai.MODEL_REGISTRY)
    for name, digest in gt_ai.MODEL_SHA256.items():
        assert len(digest) == 64 and int(digest, 16) >= 0, name


def test_tampered_model_rejected(tmp_path):
    fake = tmp_path / "RealESRGAN_x4plus.pth"
    fake.write_bytes(b"malicious pickle")
    assert gt_ai.verify_model_file(fake) is False


def test_ensure_model_discards_mismatching_download(tmp_path, monkeypatch):
    dest = tmp_path / "u2net.onnx"
    monkeypatch.setitem(gt_ai.MODEL_REGISTRY, "u2net.onnx", ("https://example.invalid/u2net.onnx", dest, []))

    def fake_urlopen(req, timeout=180):
        class R(io.BytesIO):
            status = 200
            headers = {"Content-Length": "9"}

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False
        return R(b"tampered!")

    monkeypatch.setattr(gt_ai, "_safe_urlopen", fake_urlopen)
    with pytest.raises(RuntimeError, match="SHA-256 mismatch"):
        gt_ai.ensure_model("u2net.onnx")
    assert not dest.exists()
    assert not dest.with_suffix(".onnx.tmp").exists()


def test_no_checksum_bypass_env():
    pkg = Path(main.__file__).parent / "gtoolbox"
    for f in pkg.rglob("*.py"):
        assert "MODEL_CHECKSUM_DISABLED" not in f.read_text(encoding="utf-8"), f


# ── Signed updates ───────────────────────────────────────────────

@pytest.fixture
def signing_key(monkeypatch):
    key = Ed25519PrivateKey.generate()
    pub = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    monkeypatch.setattr(gt_updates, "UPDATE_PUBLIC_KEY_B64", base64.b64encode(pub).decode())
    return key


def _zip(files: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    return buf.getvalue()


def _release(monkeypatch, key, zip_bytes, tag="v9.9.9", tamper_zip=False, sign=True):
    import hashlib
    name = f"G-Toolbox-{tag}-Windows.zip"
    sums = f"{hashlib.sha256(zip_bytes).hexdigest()}  {name}\n".encode()
    assets = {
        name: zip_bytes + (b"x" if tamper_zip else b""),
        "SHA256SUMS": sums,
    }
    if sign:
        assets["SHA256SUMS.sig"] = key.sign(sums)
    rel = {"tag_name": tag, "assets": [{"name": n, "browser_download_url": f"https://dl/{n}"} for n in assets]}
    monkeypatch.setattr(gt_updates, "_latest_release", lambda: rel)
    monkeypatch.setattr(gt_updates, "_http_get", lambda url, **kw: assets[url.rsplit("/", 1)[1]])


def test_manifest_signature_valid_and_tampered(signing_key):
    sums = b"a" * 64 + b"  file.zip\n"
    sig = signing_key.sign(sums)
    assert gt_updates.verify_release_manifest(sums, sig) == {"file.zip": "a" * 64}
    assert gt_updates.verify_release_manifest(sums, base64.b64encode(sig)) == {"file.zip": "a" * 64}
    with pytest.raises(RuntimeError, match="signature is invalid"):
        gt_updates.verify_release_manifest(sums.replace(b"a", b"b", 1), sig)


def test_safe_extract_zip_blocks_traversal(tmp_path):
    zp = tmp_path / "evil.zip"
    zp.write_bytes(_zip({"../../escape.py": "x"}))
    with pytest.raises(RuntimeError, match="Unsafe path"):
        gt_updates.safe_extract_zip(zp, tmp_path / "out")
    assert not (tmp_path.parent / "escape.py").exists()


def test_update_applies_signed_release(local_client, signing_key, monkeypatch, tmp_path):
    monkeypatch.setattr(gt_updates, "BASE_DIR", tmp_path)
    _release(monkeypatch, signing_key, _zip({"G-Toolbox/main.py": "# new", "G-Toolbox/runtime/x.py": "no"}))
    r = local_client.post("/apply-update")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "success"
    assert (tmp_path / "main.py").read_text() == "# new"
    assert not (tmp_path / "runtime").exists()


def test_update_rejects_unsigned_release(local_client, signing_key, monkeypatch, tmp_path):
    monkeypatch.setattr(gt_updates, "BASE_DIR", tmp_path)
    _release(monkeypatch, signing_key, _zip({"main.py": "# new"}), sign=False)
    r = local_client.post("/apply-update")
    assert r.status_code == 500 and "refusing" in r.json()["message"]
    assert not (tmp_path / "main.py").exists()


def test_update_rejects_tampered_zip(local_client, signing_key, monkeypatch, tmp_path):
    monkeypatch.setattr(gt_updates, "BASE_DIR", tmp_path)
    _release(monkeypatch, signing_key, _zip({"main.py": "# new"}), tamper_zip=True)
    r = local_client.post("/apply-update")
    assert r.status_code == 500 and "checksum" in r.json()["message"]
    assert not (tmp_path / "main.py").exists()


def test_update_rejects_wrong_key(local_client, monkeypatch, tmp_path):
    monkeypatch.setattr(gt_updates, "BASE_DIR", tmp_path)
    _release(monkeypatch, Ed25519PrivateKey.generate(), _zip({"main.py": "# new"}))
    r = local_client.post("/apply-update")
    assert r.status_code == 500 and "signature" in r.json()["message"]


def test_update_noop_when_current(local_client, signing_key, monkeypatch):
    _release(monkeypatch, signing_key, _zip({"main.py": "x"}), tag="v" + gt_config.APP_VERSION)
    r = local_client.post("/apply-update")
    assert r.json()["status"] == "up_to_date"


def test_embedded_key_matches_local_signing_key():
    key_path = Path.home() / ".config" / "g-toolbox" / "release-signing-key.pem"
    if not key_path.exists():
        pytest.skip("release signing key not present on this machine")
    key = serialization.load_pem_private_key(key_path.read_bytes(), password=None)
    pub = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    assert base64.b64encode(pub).decode() == gt_updates.UPDATE_PUBLIC_KEY_B64
