"""Phase 3 functional regression tests (uses the real ffmpeg when available)."""
import io
import json
import shutil
import subprocess
import time
import zipfile

import pyAesCrypt
import pytest
from PIL import Image, ImageSequence

import main

needs_ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *args], check=True)


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,sample_rate:format=duration",
                          "-of", "json", str(path)], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


@pytest.fixture(scope="module")
def media(tmp_path_factory):
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg not installed")
    d = tmp_path_factory.mktemp("media")
    ffmpeg("-f", "lavfi", "-i", "sine=f=440:sample_rate=48000", "-t", "2", str(d / "a48k.wav"))
    ffmpeg("-f", "lavfi", "-i", "testsrc=size=160x120:rate=10", "-f", "lavfi", "-i", "sine=f=440:sample_rate=48000",
           "-t", "2", "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(d / "v.mp4"))
    ffmpeg("-f", "lavfi", "-i", "testsrc=size=160x120:rate=10", "-f", "lavfi", "-i", "sine=f=440:sample_rate=48000",
           "-t", "2", "-shortest", "-c:v", "libvpx", "-c:a", "libvorbis", str(d / "v.webm"))
    (d / "sub.srt").write_text("1\n00:00:00,000 --> 00:00:01,500\nMerhaba\n", encoding="utf-8")
    return d


def duration(resp_bytes, tmp_path, ext):
    f = tmp_path / f"out.{ext}"
    f.write_bytes(resp_bytes)
    info = probe(f)
    return float(info["format"]["duration"]), info


# ── H3: metadata stripping keeps fidelity ────────────────────────

def _strip(client, data, name):
    r = client.post("/strip-metadata", files={"file": (name, data, "application/octet-stream")})
    assert r.status_code == 200, r.text
    return Image.open(io.BytesIO(r.content)), r


def test_strip_removes_exif_and_gps(local_client):
    im = Image.new("RGB", (32, 16), (10, 200, 30))
    exif = im.getexif()
    exif[0x010F] = "SecretCam"
    exif[0x8825] = {1: "N", 2: (41.0, 0.0, 0.0)}
    buf = io.BytesIO()
    im.save(buf, "JPEG", exif=exif, quality=90, comment=b"private comment")
    out, r = _strip(local_client, buf.getvalue(), "p.jpg")
    assert len(out.getexif()) == 0
    assert b"SecretCam" not in r.content and b"private comment" not in r.content
    assert r.headers["content-type"] == "image/jpeg"


def test_strip_keeps_jpeg_quantization(local_client):
    im = Image.effect_noise((64, 64), 40).convert("RGB")
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=93, exif=Image.Exif())
    orig = Image.open(io.BytesIO(buf.getvalue()))
    out, _ = _strip(local_client, buf.getvalue(), "q.jpg")
    assert out.quantization == orig.quantization


def test_strip_bakes_orientation(local_client):
    im = Image.new("RGB", (40, 20), (255, 0, 0))
    exif = im.getexif()
    exif[0x0112] = 6  # rotate 90°
    buf = io.BytesIO()
    im.save(buf, "JPEG", exif=exif)
    out, _ = _strip(local_client, buf.getvalue(), "o.jpg")
    assert out.size == (20, 40)
    assert 0x0112 not in out.getexif()


def test_strip_keeps_palette_and_transparency(local_client):
    p = Image.new("P", (4, 4))
    p.putpalette([255, 0, 0, 0, 255, 0] + [0] * 762)
    p.putpixel((1, 1), 1)
    buf = io.BytesIO()
    p.save(buf, "PNG", transparency=1)
    out, _ = _strip(local_client, buf.getvalue(), "pal.png")
    assert out.mode == "P"
    assert out.convert("RGB").getpixel((0, 0)) == (255, 0, 0)
    assert out.info.get("transparency") == 1


def test_strip_keeps_gif_animation(local_client):
    frames = [Image.new("P", (8, 8), i) for i in range(3)]
    for f in frames:
        f.putpalette([0, 0, 0, 255, 0, 0, 0, 255, 0] + [0] * 759)
    buf = io.BytesIO()
    frames[0].save(buf, "GIF", save_all=True, append_images=frames[1:], duration=120, loop=0,
                   comment=b"tracking-id-123")
    out, r = _strip(local_client, buf.getvalue(), "anim.gif")
    assert out.n_frames == 3
    assert b"tracking-id-123" not in r.content
    assert [f.convert("RGB").getpixel((0, 0)) for f in ImageSequence.Iterator(out)] == \
        [(0, 0, 0), (255, 0, 0), (0, 255, 0)]


# ── H4: subtitles with special characters ───────────────────────

@needs_ffmpeg
@pytest.mark.parametrize("sub_name", ["Ali'nin altyazısı.srt", "a:b;c,[x].srt", "normal.srt"])
def test_burn_subtitles_special_names(local_client, media, sub_name):
    r = local_client.post("/burn-subtitles", files={
        "video": ("v.mp4", (media / "v.mp4").read_bytes(), "video/mp4"),
        "subtitle": (sub_name, (media / "sub.srt").read_bytes(), "text/plain")})
    assert r.status_code == 200, r.text[:300]
    assert r.headers["content-type"] == "video/mp4"


@needs_ffmpeg
def test_burn_subtitles_rejects_non_subtitle(local_client, media):
    r = local_client.post("/burn-subtitles", files={
        "video": ("v.mp4", (media / "v.mp4").read_bytes(), "video/mp4"),
        "subtitle": ("x.exe", b"MZ", "application/octet-stream")})
    assert r.status_code == 400


# ── H5: speed / pitch use the real sample rate ──────────────────

@needs_ffmpeg
def test_nightcore_on_48k(local_client, media, tmp_path):
    r = local_client.post("/audio-effects", files={"file": ("a.wav", (media / "a48k.wav").read_bytes(), "audio/wav")},
                          data={"preset": "nightcore"})
    assert r.status_code == 200
    dur, info = duration(r.content, tmp_path, "mp3")
    assert dur == pytest.approx(2 / 1.25, abs=0.08)
    assert info["streams"][0]["sample_rate"] == "48000"


@needs_ffmpeg
def test_pitch_only_keeps_duration(local_client, media, tmp_path):
    r = local_client.post("/audio-effects", files={"file": ("a.wav", (media / "a48k.wav").read_bytes(), "audio/wav")},
                          data={"preset": "custom", "tempo": "1.0", "pitch": "1.5"})
    assert r.status_code == 200
    dur, _ = duration(r.content, tmp_path, "mp3")
    assert dur == pytest.approx(2.0, abs=0.08)


def test_atempo_chain_ranges():
    assert main.atempo_chain(1.0) == "atempo=1.000000"
    assert main.atempo_chain(0.25) == "atempo=0.5,atempo=0.500000"
    assert main.atempo_chain(3.0) == "atempo=2.0,atempo=1.500000"


# ── H6: noise reduction range and containers ────────────────────

@needs_ffmpeg
def test_denoise_clamps_out_of_range(local_client, media):
    r = local_client.post("/clean-audio-noise", files={"file": ("a.wav", (media / "a48k.wav").read_bytes(), "audio/wav")},
                          data={"noise_reduction_db": "100"})
    assert r.status_code == 200, r.text[:300]


@needs_ffmpeg
def test_denoise_webm_video(local_client, media, tmp_path):
    r = local_client.post("/clean-audio-noise", files={"file": ("v.webm", (media / "v.webm").read_bytes(), "video/webm")})
    assert r.status_code == 200, r.text[:300]
    _, info = duration(r.content, tmp_path, "webm")
    assert {s["codec_type"] for s in info["streams"]} == {"video", "audio"}


# ── H7: PDF page ranges ─────────────────────────────────────────

def _pdf(pages):
    from pypdf import PdfWriter
    w = PdfWriter()
    for _ in range(pages):
        w.add_blank_page(100, 100)
    buf = io.BytesIO()
    w.write(buf)
    return buf.getvalue()


@pytest.mark.parametrize("spec,expected", [
    ("2-", [1, 2, 3, 4]), ("-2", [0, 1]), ("1, 3-4", [0, 2, 3]), ("4-2", [1, 2, 3]), ("9", None), ("x", None),
])
def test_parse_page_ranges(spec, expected):
    if expected is None:
        with pytest.raises(ValueError):
            main.parse_page_ranges(spec, 5)
    else:
        assert main.parse_page_ranges(spec, 5) == expected


def test_pdf_split_open_range(local_client):
    from pypdf import PdfReader
    r = local_client.post("/pdf-split", files={"file": ("d.pdf", _pdf(5), "application/pdf")}, data={"page_ranges": "4-"})
    assert r.status_code == 200
    assert len(PdfReader(io.BytesIO(r.content)).pages) == 2
    bad = local_client.post("/pdf-split", files={"file": ("d.pdf", _pdf(5), "application/pdf")}, data={"page_ranges": "abc"})
    assert bad.status_code == 400


# ── H8: SRT timestamps ──────────────────────────────────────────

@pytest.mark.parametrize("sec,expected", [
    (1.9996, "00:00:02,000"), (0, "00:00:00,000"), (3661.5, "01:01:01,500"), (59.9999, "00:01:00,000")])
def test_format_timestamp(sec, expected):
    assert main.format_timestamp(sec) == expected


# ── H10: unique files and safe vault archives ───────────────────

def test_encrypt_decrypt_roundtrip_and_unique_paths(local_client, tmp_path):
    a = local_client.post("/encrypt-file", files=[("files", ("same.txt", b"first", "text/plain"))], data={"password": "pw"})
    b = local_client.post("/encrypt-file", files=[("files", ("same.txt", b"second", "text/plain"))], data={"password": "pw"})
    assert a.status_code == b.status_code == 200
    assert 'filename="same.txt.enc"' in a.headers["content-disposition"]
    d = local_client.post("/decrypt-file", files={"file": ("same.txt.enc", b.content, "application/octet-stream")},
                          data={"password": "pw"})
    assert d.content == b"second"


def test_vault_archive_has_no_traversal(local_client, tmp_path):
    r = local_client.post("/encrypt-file", data={"password": "pw"}, files=[
        ("files", ("../../evil.txt", b"x", "text/plain")),
        ("files", ("folder/C:/ok.txt", b"y", "text/plain"))])
    assert r.status_code == 200
    enc, dec = tmp_path / "v.enc", tmp_path / "v.zip"
    enc.write_bytes(r.content)
    pyAesCrypt.decryptFile(str(enc), str(dec), "pw", 64 * 1024)
    names = zipfile.ZipFile(dec).namelist()
    assert names == ["evil.txt", "folder/_/ok.txt"]  # ".." dropped, drive letter neutralised


# ── H14: animation parameter validation, task purge ─────────────

@needs_ffmpeg
def test_video_to_anim(local_client, media):
    files = {"file": ("v.mp4", (media / "v.mp4").read_bytes(), "video/mp4")}
    assert local_client.post("/video-to-anim", files=files, data={"start_time": "-i /etc/passwd"}).status_code == 400
    r = local_client.post("/video-to-anim", files=files, data={"start_time": "00:00:00.5", "duration": "1", "fps": "999"})
    assert r.status_code == 200
    assert Image.open(io.BytesIO(r.content)).format == "GIF"


def test_purge_finished_download_tasks(tmp_path):
    f = tmp_path / "old.mp4"
    f.write_bytes(b"x")
    main._download_tasks["old"] = {"created": time.time() - 7 * 3600, "status": "done", "filepath": str(f)}
    main._download_tasks["running"] = {"created": time.time() - 7 * 3600, "status": "downloading"}
    main.purge_finished_download_tasks()
    assert "old" not in main._download_tasks and not f.exists()
    assert "running" in main._download_tasks
    main._download_tasks.pop("running")
