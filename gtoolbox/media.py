"""ffmpeg / Pillow helpers used by the media tools."""

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional

import ffmpeg
from PIL import Image

from .config import ALL_TARGET_FORMATS, BASE_DIR, logger


def _find_ffmpeg() -> str | None:
    """Locates the ffmpeg executable in the system PATH or known local directories."""
    ffmpeg_in_path = shutil.which("ffmpeg")
    if ffmpeg_in_path:
        return str(Path(ffmpeg_in_path).parent)


    known_locations = [
        Path(r"C:\Program Files\ShareX\ffmpeg.exe"),
        Path(r"C:\Program Files (x86)\ShareX\ffmpeg.exe"),
        BASE_DIR / "ffmpeg.exe",
        BASE_DIR / "ffmpeg" / "ffmpeg.exe",
        BASE_DIR / "bin" / "ffmpeg.exe",
    ]
    for loc in known_locations:
        if loc.exists():
            return str(loc.parent)

    return None


FFMPEG_DIR = _find_ffmpeg()


if FFMPEG_DIR:
    if FFMPEG_DIR not in os.environ.get("PATH", ""):
        os.environ["PATH"] = FFMPEG_DIR + os.pathsep + os.environ.get("PATH", "")
    logger.info(f"✅ ffmpeg found and added to PATH: {FFMPEG_DIR}")
else:
    logger.warning(
        "⚠️ ffmpeg not found! Video download (merge/convert) may not work. "
        "Place ffmpeg.exe in the project directory or add it to PATH."
    )


def _normalize_target_format(raw: str) -> Optional[str]:
    """Returns a whitelisted lowercase extension, or None if not supported."""
    fmt = str(raw or "").strip().lower().lstrip(".")
    return fmt if fmt in ALL_TARGET_FORMATS else None


def ffmpeg_exe(tool: str = "ffmpeg") -> str:
    """Path to ffmpeg/ffprobe: the detected FFMPEG_DIR first, then PATH."""
    if FFMPEG_DIR:
        found = shutil.which(tool, path=FFMPEG_DIR)
        if found:
            return found
    return shutil.which(tool) or tool


# Long media jobs: generous limit so real-world files are not killed mid-way.
MEDIA_JOB_TIMEOUT = 3 * 3600


def ffmpeg_error(proc, label: str) -> RuntimeError:
    """Short, useful error from an ffmpeg run (drops the version banner)."""
    lines = [l for l in (proc.stderr or proc.stdout or "").splitlines() if l.strip()]
    return RuntimeError(f"{label}: " + " | ".join(lines[-4:]) if lines else f"{label} (exit {proc.returncode})")


def probe_sample_rate(path, default: int = 44100) -> int:
    """Returns the first audio stream's sample rate (ffprobe), or `default`."""
    try:
        res = subprocess.run(
            [ffmpeg_exe("ffprobe"), "-v", "error", "-select_streams", "a:0",
             "-show_entries", "stream=sample_rate", "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, timeout=60,
        )
        rate = int(res.stdout.strip().splitlines()[0])
        return rate if rate > 0 else default
    except Exception:
        return default


def atempo_chain(factor: float) -> str:
    """atempo only accepts 0.5–2.0 per instance; chain instances for other factors."""
    factor = max(0.125, min(8.0, float(factor)))
    parts = []
    while factor > 2.0:
        parts.append("atempo=2.0")
        factor /= 2.0
    while factor < 0.5:
        parts.append("atempo=0.5")
        factor /= 0.5
    parts.append(f"atempo={factor:.6f}")
    return ",".join(parts)


def speed_pitch_filter(sample_rate: int, tempo: float, pitch: float) -> str:
    """ffmpeg filter giving playback speed `tempo` and pitch factor `pitch`.

    asetrate scales speed *and* pitch by `pitch`; atempo then corrects the speed
    to `tempo`; aresample restores the original sample rate.
    """
    if abs(pitch - 1.0) < 1e-3:
        return atempo_chain(tempo)
    new_rate = int(round(sample_rate * pitch))
    return f"asetrate={new_rate},aresample={sample_rate},{atempo_chain(tempo / pitch)}"


def parse_page_ranges(spec: str, total_pages: int) -> list:
    """Parses "1-3, 5, 8-" (open-ended allowed) into sorted 0-based page indexes.

    Raises ValueError with a user-facing message on malformed input.
    """
    pages = set()
    for raw in str(spec or "").split(","):
        part = raw.strip()
        if not part:
            continue
        m = re.fullmatch(r"(\d*)\s*-\s*(\d*)", part)
        if m:
            start = int(m.group(1)) if m.group(1) else 1
            end = int(m.group(2)) if m.group(2) else total_pages
            if start > end:
                start, end = end, start
        elif part.isdigit():
            start = end = int(part)
        else:
            raise ValueError(f"Invalid page range: '{part}'")
        start, end = max(1, start), min(total_pages, end)
        pages.update(range(start - 1, end))
    if not pages:
        raise ValueError(f"No valid pages selected (document has {total_pages} pages).")
    return sorted(pages)


def _convert_image(src: str, dst: str, fmt: str) -> None:
    """Converts image formats using Pillow safely handling all color modes."""
    img = Image.open(src)
    try:
        from PIL import ImageOps
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    if fmt in ("jpg", "jpeg", "bmp"):
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

    elif fmt == "ico":
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")
        img.thumbnail((256, 256), Image.LANCZOS)

    elif fmt in ("png", "webp"):
        if img.mode == "CMYK":
            img = img.convert("RGB")

    pillow_fmt = fmt.upper()
    if pillow_fmt == "JPG":
        pillow_fmt = "JPEG"

    img.save(dst, format=pillow_fmt)


def _convert_media(src: str, dst: str) -> None:
    """Converts video and audio media formats using ffmpeg-python with error diagnostics."""
    try:
        (
            ffmpeg
            .input(src)
            .output(dst)
            .overwrite_output()
            .run(quiet=True, capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        err_msg = e.stderr.decode('utf-8', errors='ignore') if e.stderr else str(e)
        logger.error(f"FFmpeg conversion error: {err_msg}")
        raise RuntimeError(f"FFmpeg conversion failed: {err_msg[:200]}")


def _guess_media_type(ext: str) -> str:
    """Guesses MIME type based on file extension."""
    mapping = {
        "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "webp": "image/webp", "bmp": "image/bmp", "gif": "image/gif",
        "tiff": "image/tiff", "tif": "image/tiff", "ico": "image/x-icon",
        "mp4": "video/mp4", "avi": "video/x-msvideo", "mkv": "video/x-matroska",
        "mov": "video/quicktime", "webm": "video/webm",
        "mp3": "audio/mpeg", "wav": "audio/wav", "ogg": "audio/ogg",
        "flac": "audio/flac", "aac": "audio/aac", "m4a": "audio/mp4",
    }
    return mapping.get(ext, "application/octet-stream")


def format_timestamp(seconds: float) -> str:
    """Formats float seconds into SRT timestamp HH:MM:SS,mmm."""
    total_ms = max(0, int(round(float(seconds) * 1000)))  # round once, then split
    hrs, rem = divmod(total_ms, 3_600_000)
    mins, rem = divmod(rem, 60_000)
    secs, msecs = divmod(rem, 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{msecs:03d}"


# Image.info keys that carry no identifying data and are needed to reproduce the
# image faithfully (palette transparency, animation timing, colour profile).
_SAFE_INFO_KEYS = {"transparency", "duration", "loop", "background", "disposal", "dpi", "icc_profile"}


def _safe_info(info: dict) -> dict:
    return {k: v for k, v in info.items() if k in _SAFE_INFO_KEYS}


def strip_image_metadata(src, dest: Path) -> str:
    """Removes EXIF/GPS/XMP/IPTC/comments/text chunks; returns the Pillow format used.

    Preserves pixels, palette, transparency, animation frames and ICC profile.
    JPEGs are re-saved with their original quantisation tables (quality="keep")
    whenever no rotation is needed, so there is no generational quality loss.
    """
    from PIL import ImageOps, ImageSequence

    image = Image.open(src)
    fmt = (image.format or "PNG").upper()
    if fmt == "MPO":  # iPhone/camera JPEGs with an embedded preview
        fmt = "JPEG"
    n_frames = getattr(image, "n_frames", 1)

    if n_frames > 1 and fmt in ("GIF", "WEBP", "PNG"):
        frames, durations = [], []
        for frame in ImageSequence.Iterator(image):
            durations.append(frame.info.get("duration", 100))
            f = frame.copy()
            f.info = _safe_info(frame.info)
            frames.append(f)
        kwargs = {"save_all": True, "append_images": frames[1:], "duration": durations,
                  "loop": image.info.get("loop", 0)}
        if fmt == "WEBP":
            kwargs["lossless"] = True
        frames[0].save(dest, format=fmt, **kwargs)
        return fmt

    orientation = image.getexif().get(0x0112, 1)
    icc = image.info.get("icc_profile")

    if fmt == "JPEG" and orientation in (1, None):
        image.info = _safe_info(image.info)
        image.save(dest, format="JPEG", quality="keep", **({"icc_profile": icc} if icc else {}))
        return fmt

    clean = ImageOps.exif_transpose(image)  # bake the orientation into the pixels
    clean.info = _safe_info(image.info)
    kwargs = {"icc_profile": icc} if icc else {}
    if fmt == "JPEG":
        if clean.mode not in ("RGB", "L", "CMYK"):
            clean = clean.convert("RGB")
        kwargs.update(quality=95, subsampling=0)
    elif fmt == "WEBP":
        kwargs["lossless"] = True
    clean.save(dest, format=fmt, **kwargs)
    return fmt
