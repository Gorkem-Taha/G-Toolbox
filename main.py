"""
G-Toolbox — Multi-purpose Media/File Processing Toolbox
Backend: FastAPI + Jinja2 + Pillow + ffmpeg-python + rembg + yt-dlp
"""

import asyncio
import gc
import glob
import logging
import os
import re
import shutil
import subprocess
import sys
import socket
import time
import traceback
import uuid
import pyAesCrypt
from fastapi import HTTPException
from pathlib import Path

# Set global socket default timeout to 180s to prevent premature read timeouts on slow networks
socket.setdefaulttimeout(180)

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
    RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", BASE_DIR))
else:
    BASE_DIR = Path(__file__).resolve().parent
    RESOURCE_DIR = BASE_DIR

UPLOAD_DIR = BASE_DIR / "uploads"
DOWNLOAD_DIR = BASE_DIR / "downloads"
UPLOAD_DIR.mkdir(exist_ok=True)
DOWNLOAD_DIR.mkdir(exist_ok=True)

import ffmpeg
import yt_dlp
from PIL import Image, ExifTags
try:
    from rembg import remove as rembg_remove
    REMBG_AVAILABLE = True
except ImportError:
    rembg_remove = None
    REMBG_AVAILABLE = False

from typing import List, Optional, Dict, Any
import zipfile
import urllib.request
import ssl

try:
    import certifi
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
except ImportError:
    pass

logger = logging.getLogger("uvicorn.error")


def _patch_pillow_compatibility():
    """Patches PIL.Image.Image to restore backward-compatibility for AI libraries.
    Starting with Pillow 10.1.0+, Image.mode is a read-only property without a setter.
    Legacy AI libraries (rembg, u2net, basicsr, etc.) that assign img.mode directly throw:
    AttributeError: can't set attribute 'mode'.
    This patch safely restores the mode setter.
    """
    try:
        from PIL import Image
        try:
            test_im = Image.new("RGB", (1, 1))
            test_im.mode = "RGB"
        except (AttributeError, TypeError):
            fget = Image.Image.mode.fget
            def fset(self, value):
                self._mode = value
            Image.Image.mode = property(fget, fset)
            logger.info("🔧 Pillow Image.mode property setter backward-compatibility patch applied.")
    except Exception as e:
        logger.debug(f"Pillow compatibility patch notice: {e}")


_patch_pillow_compatibility()

_AI_INSTALL_PROGRESS = {
    "status": "idle",
    "progress": 0,
    "current_model": "",
    "error": None
}


def _safe_urlopen(req: urllib.request.Request, timeout: int = 180):
    """Safely opens a URL with SSL certificate fallback and generous timeout for clean Windows installations."""
    # 1. Try standard / certifi SSL context
    try:
        ctx = None
        try:
            import certifi
            ctx = ssl.create_default_context(cafile=certifi.where())
        except Exception:
            pass
        return urllib.request.urlopen(req, timeout=timeout, context=ctx) if ctx else urllib.request.urlopen(req, timeout=timeout)
    except Exception as e:
        err_str = str(e)
        if "CERTIFICATE_VERIFY_FAILED" in err_str or "certificate" in err_str.lower() or "ssl" in err_str.lower():
            logger.warning(f"SSL certificate verification failed ({e}). Retrying with unverified context fallback...")
            try:
                unverified_ctx = ssl._create_unverified_context()
                return urllib.request.urlopen(req, timeout=timeout, context=unverified_ctx)
            except Exception as retry_err:
                raise retry_err from e
        raise e


GITHUB_REPO_URL = "https://github.com/Gorkem-Taha/G-Toolbox/archive/refs/heads/main.zip"

os.environ.setdefault("U2NET_HOME", str(Path.home() / ".u2net"))
os.environ.setdefault("TORCH_HOME", str(Path.home() / ".cache" / "torch"))

SimpleLama = None
LAMA_AVAILABLE = False
_LAMA_INSTANCE = None

cv2 = None
np = None
torch = None
RRDBNet = None
RealESRGANer = None
_UPSCALER_INSTANCE = None
_UPSCALER_INSTANCES = {}


def ensure_ai_runtime() -> bool:
    """Dynamically verifies and imports AI frameworks (Torch, RealESRGAN, BasicSR, Rembg, LaMa, Whisper, Demucs).
    Ensures hotfixes are applied and libraries installed during app runtime are immediately accessible without restart.
    """
    global torch, cv2, np, RRDBNet, RealESRGANer, SimpleLama, LAMA_AVAILABLE, rembg_remove, REMBG_AVAILABLE

    # 0. Ensure runtime/Lib/site-packages is present in sys.path (critical for portable Python)
    try:
        runtime_sp = BASE_DIR / "runtime" / "Lib" / "site-packages"
        if runtime_sp.exists() and str(runtime_sp) not in sys.path:
            sys.path.insert(0, str(runtime_sp))
    except Exception:
        pass

    # 0.1 Ensure Pillow Image.mode setter is active
    _patch_pillow_compatibility()

    # 1. Hotfix: basicsr requires torchvision.transforms.functional_tensor
    try:
        import torchvision.transforms.functional_tensor
    except ImportError:
        try:
            import torchvision.transforms.functional as functional
            sys.modules['torchvision.transforms.functional_tensor'] = functional
        except Exception:
            pass

    # 2. PyTorch & RealESRGAN
    if RealESRGANer is None or torch is None:
        try:
            import torch as _t
            import cv2 as _c
            import numpy as _n
            from basicsr.archs.rrdbnet_arch import RRDBNet as _RRDBNet
            from realesrgan import RealESRGANer as _RealESRGANer

            torch = _t
            cv2 = _c
            np = _n
            RRDBNet = _RRDBNet
            RealESRGANer = _RealESRGANer
            logger.info("✅ RealESRGAN & PyTorch runtime loaded successfully.")
        except Exception as e:
            logger.debug(f"AI upscaler dynamic load: {e}")

    # 3. Rembg
    if not REMBG_AVAILABLE or rembg_remove is None:
        try:
            from rembg import remove as _rembg_remove
            rembg_remove = _rembg_remove
            REMBG_AVAILABLE = True
            logger.info("✅ Rembg runtime loaded successfully.")
        except Exception as e:
            logger.debug(f"Rembg dynamic load: {e}")

    # 4. SimpleLama
    if not LAMA_AVAILABLE or SimpleLama is None:
        try:
            from simple_lama_inpainting import SimpleLama as _SimpleLama
            SimpleLama = _SimpleLama
            LAMA_AVAILABLE = True
            logger.info("✅ SimpleLama runtime loaded successfully.")
        except Exception as e:
            logger.debug(f"SimpleLama dynamic load: {e}")

    return bool(torch and RealESRGANer)


# Initial load attempt on server startup
try:
    ensure_ai_runtime()
except Exception as _e:
    logger.debug(f"Initial AI runtime check notice: {_e}")



def get_lama_model():
    global _LAMA_INSTANCE
    if _LAMA_INSTANCE is None:
        ensure_ai_runtime()
        if not LAMA_AVAILABLE or SimpleLama is None:
            raise RuntimeError("simple-lama-inpainting kütüphanesi henüz yüklü değil. Lütfen yapay zeka kurulumunu tamamlayın.")
        _LAMA_INSTANCE = SimpleLama()
    return _LAMA_INSTANCE


def get_upscaler(model_type: str = "general", force_fp32: bool = False):
    global _UPSCALER_INSTANCE, _UPSCALER_INSTANCES
    ensure_ai_runtime()
    if RealESRGANer is None:
        raise RuntimeError("realesrgan veya PyTorch henüz yüklü değil. Lütfen yapay zeka kurulumunu tamamlayın.")

    m_key = "anime" if "anime" in str(model_type).lower() else "general"
    cache_key = f"{m_key}_fp32" if force_fp32 else m_key

    # Return cached singleton if already loaded and not forcing FP32 fallback
    if cache_key in _UPSCALER_INSTANCES and not force_fp32:
        return _UPSCALER_INSTANCES[cache_key]

    import urllib.request

    if m_key == "anime":
        model_name = "RealESRGAN_x4plus_anime_6B.pth"
        model_url = f"https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/{model_name}"
        expected_min_size = 15 * 1024 * 1024  # ~17.9 MB
        num_block = 6
    else:
        model_name = "RealESRGAN_x4plus.pth"
        model_url = f"https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/{model_name}"
        expected_min_size = 60 * 1024 * 1024  # ~67 MB
        num_block = 23

    model_path = BASE_DIR / model_name

    # Verify existing file integrity to prevent _pickle.UnpicklingError from partial downloads
    if model_path.exists() and model_path.stat().st_size < expected_min_size:
        logger.warning(f"Incomplete model file detected ({model_path.stat().st_size} bytes). Removing and re-downloading...")
        try:
            model_path.unlink()
        except Exception as e:
            logger.error(f"Could not remove corrupted model file: {e}")

    if not model_path.exists():
        logger.info(f"Downloading {model_name} from {model_url}...")
        _download_chunked_file(model_url, model_path, expected_min_size, 0, 100, model_name)
        logger.info(f"Successfully downloaded and verified {model_name} ({model_path.stat().st_size} bytes).")

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=num_block, num_grow_ch=32, scale=4)
    
    # Half-precision (FP16) produces NaN / black images on GTX 16xx Turing and older Pascal cards
    half = False
    if torch.cuda.is_available() and not force_fp32:
        try:
            gpu_name = torch.cuda.get_device_name(0).lower()
            if not any(x in gpu_name for x in ["1650", "1660", "gtx 10", "gtx 9"]):
                half = True
        except Exception:
            half = False

    tile_size = 256 if (torch.cuda.is_available() and half) else 192

    upscaler_model = RealESRGANer(
        scale=4,
        model_path=str(model_path),
        model=model,
        tile=tile_size,
        tile_pad=10,
        pre_pad=0,
        half=half,
        device=device
    )

    if not force_fp32:
        _UPSCALER_INSTANCES[cache_key] = upscaler_model
        _UPSCALER_INSTANCE = upscaler_model
    return upscaler_model

from fastapi import BackgroundTasks, FastAPI, File, Form, UploadFile, Request, Header
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

logger = logging.getLogger("uvicorn.error")


def _safe_filename(raw: str) -> str:
    """Sanitizes the filename by removing dangerous characters and path traversal attempts."""
    name = Path(raw).name
    if not name or name.startswith("."):
        name = uuid.uuid4().hex
    return name

def cleanup_files_and_memory(*filepaths):
    """Safely deletes specified files from disk and triggers garbage collection to free up system memory and VRAM."""
    import gc
    
    for path in filepaths:
        if path and os.path.exists(str(path)):
            try:
                os.remove(str(path))
            except Exception as e:
                logger.warning(f"Failed to delete file: {path} - Error: {e}")
                
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
    except ImportError:
        pass



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
        os.environ["PATH"] = f"{FFMPEG_DIR};{os.environ.get('PATH', '')}"
    logger.info(f"✅ ffmpeg found and added to PATH: {FFMPEG_DIR}")
else:
    logger.warning(
        "⚠️ ffmpeg not found! Video download (merge/convert) may not work. "
        "Place ffmpeg.exe in the project directory or add it to PATH."
    )

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="G-Toolbox", version="4.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    err_tb = traceback.format_exc()
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}\n{err_tb}")
    if request.url.path == "/" or "text/html" in request.headers.get("accept", ""):
        return HTMLResponse(
            status_code=500,
            content=f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>G-Toolbox Hata</title></head><body style='font-family:sans-serif;background:#0d1117;color:#c9d1d9;padding:30px;'>"
                    f"<h2 style='color:#f85149;'>⚠️ G-Toolbox — Sunucu Hatası (500)</h2>"
                    f"<p>İstek: <code>{request.method} {request.url.path}</code></p>"
                    f"<p>Hata: <b>{exc}</b></p>"
                    f"<pre style='background:#161b22;padding:15px;border-radius:6px;overflow-x:auto;color:#ff7b72;'>{err_tb}</pre>"
                    f"</body></html>"
        )
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": str(exc), "path": request.url.path}
    )

def get_lan_ip() -> str:
    """Detects the primary LAN IPv4 address of the host machine."""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

@app.get("/api/network-info")
async def get_network_info(request: Request):
    """Returns host LAN network details for easy mobile pairing."""
    host_ip = get_lan_ip()
    port = request.url.port or 8000
    return JSONResponse({
        "lan_ip": host_ip,
        "port": port,
        "mobile_url": f"http://{host_ip}:{port}"
    })

progress_store: dict[str, dict] = {}

def update_progress(task_id: str, progress: int, message: str):
    if task_id:
        import time
        if len(progress_store) > 150:
            cutoff = time.time() - 1800
            expired = [k for k, v in progress_store.items() if v.get("ts", 0) < cutoff]
            for k in expired:
                progress_store.pop(k, None)
        progress_store[task_id] = {"progress": progress, "message": message, "ts": time.time()}

@app.get("/progress/{task_id}")
async def get_progress(task_id: str):
    """Returns the current progress status for a given task ID."""
    info = progress_store.get(task_id, {"progress": 0, "message": ""})
    return JSONResponse(content={"progress": info.get("progress", 0), "message": info.get("message", "")})

def purge_stale_files(max_age_hours: int = 12):
    """Safely removes abandoned temporary files older than max_age_hours from disk."""
    import time
    now = time.time()
    cutoff = now - (max_age_hours * 3600)
    purged = 0
    for folder in [UPLOAD_DIR, DOWNLOAD_DIR]:
        if not folder.exists():
            continue
        for item in folder.iterdir():
            if item.is_file() and not item.name.startswith("."):
                try:
                    if item.stat().st_mtime < cutoff:
                        item.unlink()
                        purged += 1
                except Exception:
                    pass
    if purged > 0:
        logger.info(f"🧹 Disk maintenance: Cleaned up {purged} stale temporary file(s).")

@app.on_event("startup")
async def on_startup():
    """Application startup initialization and disk cleanup."""
    try:
        purge_stale_files(max_age_hours=6)
    except Exception as e:
        logger.warning(f"Startup purge warning: {e}")

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

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# ── Desteklenen formatlar ─────────────────────────────────────────
IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "bmp", "gif", "tiff", "ico"}
VIDEO_EXTENSIONS = {"mp4", "avi", "mkv", "mov", "webm", "flv", "wmv"}
AUDIO_EXTENSIONS = {"mp3", "wav", "ogg", "flac", "aac", "m4a", "wma"}

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


@app.get("/")
async def index(request: Request):
    """Renders the main application interface."""
    # 1. Direct file streaming (immune to Starlette 1.x / Jinja2 breaking signature changes)
    index_candidates = [
        TEMPLATES_DIR / "index.html",
        BASE_DIR / "templates" / "index.html",
        RESOURCE_DIR / "templates" / "index.html",
        BASE_DIR / "index.html",
        Path.cwd() / "templates" / "index.html",
    ]
    for candidate in index_candidates:
        if candidate.exists():
            return FileResponse(str(candidate), media_type="text/html; charset=utf-8")

    # 2. Universal Jinja2 fallback supporting Starlette 1.x and legacy Starlette
    try:
        return templates.TemplateResponse(request=request, name="index.html")
    except (TypeError, ValueError):
        try:
            return templates.TemplateResponse(request, "index.html", {"request": request})
        except (TypeError, ValueError):
            return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Uploads a file to the temporary storage directory."""
    try:
        safe_name = _safe_filename(file.filename)
        dest = UPLOAD_DIR / safe_name
        with open(dest, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "File uploaded successfully",
                "filename": safe_name,
                "size": os.path.getsize(dest),
            },
        )
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Upload error: {str(exc)}",
            },
        )


@app.post("/convert")
async def convert_file(
    file: UploadFile = File(...),
    target_format: str = Form(...),
    background_tasks: BackgroundTasks = None,
    x_task_id: str = Header(None)
):
    """Handles standard media file conversions."""
    update_progress(x_task_id, 20, "File uploaded, initializing conversion...")
    target_format = target_format.strip().lower().lstrip(".")
    uid = uuid.uuid4().hex[:8]
    safe_name = _safe_filename(file.filename)

    # Gelen dosyayı geçici olarak uploads/ klasörüne kaydet
    src_path = UPLOAD_DIR / f"{uid}_{safe_name}"
    with open(src_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Çıkış dosya adı
    stem = Path(safe_name).stem
    out_name = f"{stem}_{uid}.{target_format}"
    out_path = DOWNLOAD_DIR / out_name

    # MIME tipine göre dosya kategorisi belirle
    mime = file.content_type or ""
    category = MIME_MAP.get(mime)

    # MIME bilinmiyorsa uzantıdan tahmin et
    if not category:
        ext = Path(safe_name).suffix.lower().lstrip(".")
        if ext in IMAGE_EXTENSIONS:
            category = "image"
        elif ext in VIDEO_EXTENSIONS:
            category = "video"
        elif ext in AUDIO_EXTENSIONS:
            category = "audio"

    if not category:
        cleanup_files_and_memory(src_path)
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "Unsupported file type."},
        )

    try:
        update_progress(x_task_id, 50, "Model is executing. This process relies on CPU/GPU hardware and may take a moment...")
        if category == "image":
            _convert_image(str(src_path), str(out_path), target_format)
        else:
            _convert_media(str(src_path), str(out_path))

        media_type = _guess_media_type(target_format)
        update_progress(x_task_id, 90, "Packaging results...")
        if background_tasks:
            background_tasks.add_task(cleanup_files_and_memory, src_path, out_path)
        else:
            cleanup_files_and_memory(src_path)
            
        update_progress(x_task_id, 100, "Completed!")
        return FileResponse(
            path=str(out_path),
            filename=out_name,
            media_type=media_type,
        )

    except Exception as exc:
        cleanup_files_and_memory(src_path, out_path)
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Conversion error: {str(exc)}"},
        )


@app.post("/convert-universal")
async def convert_universal(
    file: UploadFile = File(...),
    target_format: str = Form(...),
    background_tasks: BackgroundTasks = None,
    x_task_id: str = Header(None)
):
    """Handles universal format conversions across image, audio, and video types."""
    update_progress(x_task_id, 20, "File uploaded, initializing conversion...")
    target_format = target_format.strip().lower().lstrip(".")
    uid = uuid.uuid4().hex[:8]
    safe_name = _safe_filename(file.filename)

    stem = Path(safe_name).stem
    out_name = f"{stem}_{uid}.{target_format}"
    out_path = DOWNLOAD_DIR / out_name

    src_path = UPLOAD_DIR / f"uni_{uid}_{safe_name}"
    with open(src_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    ext = Path(safe_name).suffix.lower().lstrip(".")

    images = {"png", "jpg", "jpeg", "webp", "bmp", "gif", "tiff", "ico"}
    videos_audios = {"mp4", "avi", "mkv", "mov", "webm", "flv", "wmv", "mp3", "wav", "ogg", "flac", "aac", "m4a", "wma"}

    try:
        update_progress(x_task_id, 50, "Model is executing. This may take a while depending on file size...")
        if ext in images and target_format in images:
            _convert_image(str(src_path), str(out_path), target_format)
            
        elif ext in videos_audios and target_format in videos_audios:
            _convert_media(str(src_path), str(out_path))

        else:
            cleanup_files_and_memory(src_path)
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "Unsupported universal conversion route."}
            )

        update_progress(x_task_id, 90, "Packaging results...")
        if background_tasks:
            background_tasks.add_task(cleanup_files_and_memory, src_path, out_path)
            
        update_progress(x_task_id, 100, "Completed!")
        return FileResponse(
            path=str(out_path),
            filename=out_name,
            media_type=_guess_media_type(target_format),
        )

    except Exception as exc:
        cleanup_files_and_memory(src_path, out_path)
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Conversion error: {str(exc)}"},
        )


@app.post("/remove-background")
async def remove_background(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    x_task_id: str = Header(None)
):
    """Removes the background from images using the rembg AI model."""
    ensure_ai_runtime()
    update_progress(x_task_id, 20, "File uploaded, initializing process...")
    uid = uuid.uuid4().hex[:8]
    safe_name = _safe_filename(file.filename)
    mime = file.content_type or ""
    ext = Path(safe_name).suffix.lower().lstrip(".")
    is_image = mime.startswith("image/") or ext in IMAGE_EXTENSIONS

    if not is_image:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "Only image files are accepted."},
        )

    src_path = UPLOAD_DIR / f"{uid}_{safe_name}"
    with open(src_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    stem = Path(safe_name).stem
    out_name = f"{stem}_nobg_{uid}.png"
    out_path = DOWNLOAD_DIR / out_name

    if not REMBG_AVAILABLE or rembg_remove is None:
        cleanup_files_and_memory(src_path)
        raise HTTPException(
            status_code=500,
            detail="rembg kütüphanesi henüz yüklü değil. Lütfen yapay zeka kurulumunu tamamlayın."
        )

    try:
        update_progress(x_task_id, 50, "AI model is executing. This process relies on CPU and GPU overhead...")
        img = Image.open(src_path)
        try:
            from PIL import ImageOps
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        # Convert non-RGB/RGBA modes (CMYK, P, L, 1, etc.) cleanly
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA" if "A" in img.mode or "transparency" in img.info else "RGB")

        result = rembg_remove(img)
        if isinstance(result, Image.Image):
            if result.mode != "RGBA":
                result = result.convert("RGBA")
            result.save(str(out_path), format="PNG")
        elif isinstance(result, (bytes, bytearray)):
            with open(out_path, "wb") as f:
                f.write(result)
        elif isinstance(result, np.ndarray):
            res_img = Image.fromarray(result)
            if res_img.mode != "RGBA":
                res_img = res_img.convert("RGBA")
            res_img.save(str(out_path), format="PNG")
        else:
            raise ValueError(f"Unexpected rembg output format: {type(result)}")

        update_progress(x_task_id, 90, "Packaging results...")
        if background_tasks:
            background_tasks.add_task(cleanup_files_and_memory, src_path, out_path)
        else:
            cleanup_files_and_memory(src_path)
            
        update_progress(x_task_id, 100, "Completed!")
        return FileResponse(
            path=str(out_path),
            filename=out_name,
            media_type="image/png",
        )

    except Exception as exc:
        cleanup_files_and_memory(src_path, out_path)
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Background removal error: {str(exc)}"},
        )

@app.post("/magic-erase")
async def magic_erase(
    image: UploadFile = File(...),
    mask: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    x_task_id: str = Header(None)
):
    """Erases specified masked regions from an image using the LaMa inpainting model."""
    ensure_ai_runtime()
    update_progress(x_task_id, 20, "File uploaded, initializing process...")
    if not LAMA_AVAILABLE:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "simple-lama-inpainting kütüphanesi henüz yüklü değil. Lütfen yapay zeka kurulumunu tamamlayın."}
        )

    uid = uuid.uuid4().hex[:8]
    safe_name = _safe_filename(image.filename)
    
    img_path = UPLOAD_DIR / f"magic_{uid}_{safe_name}"
    mask_path = UPLOAD_DIR / f"mask_{uid}_{safe_name}"
    
    stem = Path(safe_name).stem
    out_name = f"{stem}_erased_{uid}.png"
    out_path = DOWNLOAD_DIR / out_name

    with open(img_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
        
    with open(mask_path, "wb") as buffer:
        shutil.copyfileobj(mask.file, buffer)

    try:
        update_progress(x_task_id, 50, "LaMa model is executing over the masked regions...")
        def process_lama():
            lama_model = get_lama_model()
            orig = Image.open(img_path)
            try:
                from PIL import ImageOps
                orig = ImageOps.exif_transpose(orig)
            except Exception:
                pass

            has_alpha = orig.mode == "RGBA" or "transparency" in orig.info
            orig_alpha = orig.split()[-1] if has_alpha and orig.mode == "RGBA" else None

            orig_rgb = orig.convert("RGB")
            mask_img = Image.open(mask_path).convert("L")
            if mask_img.size != orig_rgb.size:
                mask_img = mask_img.resize(orig_rgb.size, Image.NEAREST)

            result = lama_model(orig_rgb, mask_img)
            if orig_alpha is not None:
                if result.size != orig_alpha.size:
                    orig_alpha = orig_alpha.resize(result.size, Image.LANCZOS)
                result.putalpha(orig_alpha)
            result.save(out_path, format="PNG")

        await asyncio.to_thread(process_lama)

        update_progress(x_task_id, 90, "Packaging results...")
        if background_tasks:
            background_tasks.add_task(cleanup_files_and_memory, img_path, mask_path, out_path)
        else:
            cleanup_files_and_memory(img_path, mask_path)
            
        update_progress(x_task_id, 100, "Completed!")
        return FileResponse(
            path=str(out_path),
            filename=out_name,
            media_type="image/png",
        )
    except Exception as exc:
        cleanup_files_and_memory(img_path, mask_path, out_path)
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Magic erase error: {str(exc)}"},
        )




# ── AI Image Upscaler Endpoint ──────────────────────────────────
@app.post("/upscale-image")
async def upscale_image(
    file: UploadFile = File(...),
    scale: int = Form(4),
    model_type: str = Form("general"),
    background_tasks: BackgroundTasks = None,
    x_task_id: str = Header(None)
):
    ensure_ai_runtime()
    update_progress(x_task_id, 20, "Dosya yüklendi, işleme başlanıyor...")
    if RealESRGANer is None:
        return JSONResponse(status_code=500, content={"success": False, "message": "realesrgan veya PyTorch henüz yüklü değil. Lütfen yapay zeka kurulumunu tamamlayın."})
    
    if scale not in [2, 4]:
        scale = 4
        
    uid = uuid.uuid4().hex[:8]
    safe_name = _safe_filename(file.filename)
    stem = Path(safe_name).stem
    ext = Path(safe_name).suffix or ".png"
    
    src_path = UPLOAD_DIR / f"upscale_{uid}{ext}"
    out_name = f"{stem}_upscaled_{scale}x_{uid}{ext}"
    out_path = DOWNLOAD_DIR / out_name
    
    with open(src_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        update_progress(x_task_id, 50, "Model çalışıyor (Bu işlem biraz sürebilir)...")
        def process_upscale():
            upscaler = get_upscaler(model_type=model_type)
            # Decode using raw bytes to bypass cv2 unicode limitations
            img_bytes = np.fromfile(str(src_path), np.uint8)
            img = cv2.imdecode(img_bytes, cv2.IMREAD_UNCHANGED)
            if img is None:
                raise ValueError("Image could not be read or is corrupted.")
            
            # Dimension safety guard: avoid extreme resolutions causing system freeze / OOM
            h, w = img.shape[:2]
            max_dim = 3840
            if max(h, w) > max_dim:
                factor = max_dim / max(h, w)
                new_w, new_h = int(w * factor), int(h * factor)
                img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

            # Handle transparency (RGBA) and grayscale channels safely
            has_alpha = False
            alpha_channel = None

            if len(img.shape) == 2:
                # 1-channel Grayscale -> convert to 3-channel BGR
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            elif len(img.shape) == 3:
                if img.shape[2] == 4:
                    # 4-channel RGBA: extract alpha, enhance BGR, resize alpha with Lanczos
                    has_alpha = True
                    alpha_channel = img[:, :, 3]
                    img = img[:, :, :3]
                elif img.shape[2] == 1:
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                elif img.shape[2] > 4:
                    img = img[:, :, :3]

            try:
                output, _ = upscaler.enhance(img, outscale=scale)
            except Exception as e:
                # If CUDA or FP16 error occurs, retry with safe FP32 fallback
                if "half" in str(e).lower() or "cuda" in str(e).lower():
                    logger.warning(f"Upscale failed with FP16/CUDA error: {e}. Retrying with FP32 fallback...")
                    fallback_upscaler = get_upscaler(model_type=model_type, force_fp32=True)
                    output, _ = fallback_upscaler.enhance(img, outscale=scale)
                else:
                    raise e
            
            # Recombine alpha channel if original image was transparent
            if has_alpha and alpha_channel is not None:
                out_h, out_w = output.shape[:2]
                alpha_resized = cv2.resize(alpha_channel, (out_w, out_h), interpolation=cv2.INTER_LANCZOS4)
                if len(output.shape) == 3 and output.shape[2] == 3:
                    output = np.dstack([output, alpha_resized])

            # Choose safe output extension (RGBA requires PNG format)
            out_ext = ext.lower() if ext else '.png'
            if has_alpha and out_ext in ('.jpg', '.jpeg'):
                out_ext = '.png'
            
            # Encode and save via tofile to prevent Unicode save issues
            is_success, buffer = cv2.imencode(out_ext, output)
            if is_success:
                buffer.tofile(str(out_path))
            else:
                raise ValueError("Upscaled image could not be encoded.")
            
        await asyncio.to_thread(process_upscale)
        
        update_progress(x_task_id, 90, "Packaging results...")
        if background_tasks:
            background_tasks.add_task(cleanup_files_and_memory, src_path, out_path)
        else:
            cleanup_files_and_memory(src_path)
            
        update_progress(x_task_id, 100, "Completed!")
        return FileResponse(
            path=str(out_path),
            filename=out_name,
            media_type="image/png" if ext.lower() == ".png" else "image/jpeg"
        )
    except Exception as exc:
        cleanup_files_and_memory(src_path, out_path)
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Upscale error: {str(exc)}"}
        )


class VideoURLRequest(BaseModel):
    url: str

class VideoDownloadRequest(BaseModel):
    url: str
    format_id: str
    title: str = "video"


# In-memory download task tracker
_download_tasks: dict[str, dict] = {}


def _ytdlp_progress_hook(task_id: str):
    """Callback function to report yt-dlp download progress."""
    def hook(d):
        task = _download_tasks.get(task_id)
        if not task:
            return
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            if total > 0:
                task["progress"] = min(int((downloaded / total) * 95), 95)
            speed = d.get("speed")
            if speed:
                task["speed"] = speed
        elif d.get("status") == "finished":
            task["progress"] = 97  # Download finished, merging/converting
    return hook


def _build_ytdlp_opts(task_id: Optional[str] = None, out_template: Optional[str] = None, format_spec: Optional[str] = None, is_mp3: bool = False) -> dict:
    """Builds hardened yt-dlp options preventing HTTP 403 Forbidden using multi-client routing."""
    opts = {
        "socket_timeout": 30,
        "retries": 10,
        "fragment_retries": 10,
        "retry_sleep_functions": {"http": lambda n: 2},
        "quiet": False if task_id else True,
        "no_warnings": False,
        "nocheckcertificate": True,
        "prefer_insecure": False,
        "legacy_server_connect": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "ios", "mweb", "web"],
                "player_skip": ["configs", "webpage"],
            }
        },
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,tr;q=0.8",
            "Sec-Fetch-Mode": "navigate",
        },
    }
    if FFMPEG_DIR:
        opts["ffmpeg_location"] = FFMPEG_DIR
    if task_id:
        opts["progress_hooks"] = [_ytdlp_progress_hook(task_id)]
    if out_template:
        opts["outtmpl"] = out_template

    if is_mp3:
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    elif format_spec:
        opts["format"] = format_spec
        opts["merge_output_format"] = "mp4"

    return opts


@app.post("/fetch-video-info")
async def fetch_video_info(req: VideoURLRequest):
    """Fetches metadata and available resolutions for the provided video URL with 403 anti-block."""
    try:
        ydl_opts = _build_ytdlp_opts()
        ydl_opts["skip_download"] = True

        def _extract():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(req.url, download=False)
                return ydl.sanitize_info(info)

        info = await asyncio.to_thread(_extract)

        available_heights = set()
        for f in info.get("formats", []):
            h = f.get("height")
            vcodec = f.get("vcodec", "none")
            if h and vcodec != "none":
                available_heights.add(h)

        resolution_list = sorted(available_heights, reverse=True)

        duration = info.get("duration", 0)
        dur_str = f"{int(duration // 60)}:{int(duration % 60):02d}" if duration else ""

        return JSONResponse(content={
            "success": True,
            "title": info.get("title", "Unknown"),
            "thumbnail": info.get("thumbnail", ""),
            "duration": dur_str,
            "uploader": info.get("uploader", ""),
            "resolutions": resolution_list,
        })

    except Exception as exc:
        logger.error(f"fetch_video_info error: {exc}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Video bilgisi alınamadı: {str(exc)}"},
        )


@app.post("/start-download")
async def start_download(req: VideoDownloadRequest):
    """Initializes background download task with 403 protection and returns a tracking ID immediately."""
    task_id = uuid.uuid4().hex[:12]
    uid = task_id[:8]
    out_template = str(DOWNLOAD_DIR / f"{uid}.%(ext)s")

    _download_tasks[task_id] = {
        "status": "downloading",
        "progress": 0,
        "speed": 0,
        "filename": None,
        "filepath": None,
        "error": None,
    }

    if req.format_id == "mp3":
        if not FFMPEG_DIR:
            _download_tasks[task_id]["status"] = "error"
            _download_tasks[task_id]["error"] = "MP3 dönüşümü için ffmpeg bulunamadı."
            return JSONResponse(content={"success": False, "message": "ffmpeg bulunamadı, MP3 dönüştürme yapılamıyor."})
        ydl_opts = _build_ytdlp_opts(task_id=task_id, out_template=out_template, is_mp3=True)
    elif req.format_id.isdigit():
        height = req.format_id
        format_spec = (
            f"best[height={height}][vcodec!=none][acodec!=none]/"
            f"bestvideo[height={height}]+bestaudio/"
            f"best[height<={height}][vcodec!=none][acodec!=none]/"
            f"bestvideo[height<={height}]+bestaudio/best"
        )
        ydl_opts = _build_ytdlp_opts(task_id=task_id, out_template=out_template, format_spec=format_spec)
    else:
        format_spec = "best[vcodec!=none][acodec!=none]/bestvideo+bestaudio/best"
        ydl_opts = _build_ytdlp_opts(task_id=task_id, out_template=out_template, format_spec=format_spec)

    # Güvenli dosya adı oluştur
    safe_title = re.sub(r'[^\w\s-]', '', req.title).strip()
    safe_title = re.sub(r'[-\s]+', '_', safe_title)
    if not safe_title:
        safe_title = "video"

    def _do_download():
        task = _download_tasks[task_id]
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([req.url])

            # İndirilen dosyayı bul
            pattern = str(DOWNLOAD_DIR / f"{uid}.*")
            files = glob.glob(pattern)
            if not files:
                task["status"] = "error"
                task["error"] = "İndirilen dosya diskte bulunamadı."
                return

            out_file = Path(files[0])
            ext = out_file.suffix.lstrip(".")
            final_filename = f"{safe_title}.{ext}"

            task["status"] = "done"
            task["progress"] = 100
            task["filename"] = final_filename
            task["filepath"] = str(out_file)

        except Exception as exc:
            logger.error(f"Download task {task_id} failed: {exc}")
            task["status"] = "error"
            task["error"] = str(exc)
            cleanup_files_and_memory(*glob.glob(str(DOWNLOAD_DIR / f"{uid}.*")))

    asyncio.get_event_loop().run_in_executor(None, _do_download)

    return JSONResponse(content={
        "success": True,
        "task_id": task_id,
        "message": "İndirme başlatıldı.",
    })


@app.get("/download-status/{task_id}")
async def download_status(task_id: str):
    """Polls the current download status using task ID."""
    task = _download_tasks.get(task_id)
    if not task:
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Görev bulunamadı."},
        )

    speed_str = ""
    if task.get("speed"):
        spd = task["speed"]
        if spd > 1_048_576:
            speed_str = f"{spd / 1_048_576:.1f} MB/s"
        elif spd > 1024:
            speed_str = f"{spd / 1024:.0f} KB/s"

    return JSONResponse(content={
        "success": True,
        "status": task["status"],
        "progress": task["progress"],
        "speed": speed_str,
        "filename": task.get("filename"),
        "error": task.get("error"),
    })


class SaveTaskRequest(BaseModel):
    task_id: str
    suggested_name: Optional[str] = None


def _open_native_save_dialog(initial_filename: str, file_ext: str = "") -> Optional[str]:
    """Opens a native Windows Save As dialog on top of all windows without requiring Tkinter."""
    # 1. Primary Method on Windows: WinForms SaveFileDialog via PowerShell (works on all Windows versions with zero Python dependencies)
    if sys.platform == "win32":
        try:
            clean_ext = file_ext.lstrip(".")
            filter_str = f"{clean_ext.upper()} Files (*.{clean_ext})|*.{clean_ext}|All Files (*.*)|*.*" if clean_ext else "All Files (*.*)|*.*"
            safe_name = initial_filename.replace("'", "''")
            ps_cmd = (
                "[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms') | Out-Null; "
                "$f = New-Object System.Windows.Forms.SaveFileDialog; "
                f"$f.FileName = '{safe_name}'; "
                f"$f.Filter = '{filter_str}'; "
                "$f.Title = 'G-Toolbox — Dosyayı Farklı Kaydet'; "
                "$top = New-Object System.Windows.Forms.Form; "
                "$top.TopMost = $true; "
                "if ($f.ShowDialog($top) -eq [System.Windows.Forms.DialogResult]::OK) { "
                "Write-Output $f.FileName "
                "} else { Write-Output '__CANCELED__' }"
            )
            res = subprocess.run(
                ["powershell", "-Sta", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=180,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            out_str = res.stdout.strip()
            if out_str == "__CANCELED__":
                return "CANCELED"
            if out_str and os.path.isabs(out_str):
                return out_str
        except Exception as e:
            logger.warning(f"PowerShell SaveFileDialog exception: {e}")

    # 2. Secondary fallback: Tkinter (if available on standard Python distros)
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        types = []
        if file_ext:
            clean_ext = file_ext.lstrip(".")
            types.append((f"{clean_ext.upper()} Dosyaları (*.{clean_ext})", f"*.{clean_ext}"))
        types.append(("Tüm Dosyalar (*.*)", "*.*"))

        chosen_path = filedialog.asksaveasfilename(
            parent=root,
            initialfile=initial_filename,
            defaultextension=f".{file_ext.lstrip('.')}" if file_ext else None,
            filetypes=types,
            title="G-Toolbox — Dosyayı Farklı Kaydet"
        )
        root.destroy()
        return chosen_path if chosen_path else "CANCELED"
    except Exception as e:
        logger.debug(f"Tkinter dialog fallback: {e}")

    # If GUI dialog cannot be opened on this OS, return None to trigger browser stream download
    return None


@app.post("/api/save-task-file")
async def save_task_file(req: SaveTaskRequest):
    """Saves an existing completed task file via native Windows Save As dialog."""
    task = _download_tasks.get(req.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Görev bulunamadı veya süresi doldu.")

    filepath = task.get("filepath")
    if not filepath or not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="İşlenmiş dosya diskte bulunamadı.")

    filename = req.suggested_name or task.get("filename") or Path(filepath).name
    ext = Path(filepath).suffix

    chosen = await asyncio.to_thread(_open_native_save_dialog, filename, ext)
    if chosen == "CANCELED":
        return JSONResponse(content={"success": False, "canceled": True, "message": "Kaydetme iptal edildi."})
    if not chosen:
        return JSONResponse(content={"success": False, "canceled": False, "native_unsupported": True})

    try:
        shutil.copy2(filepath, chosen)
        return JSONResponse(content={
            "success": True,
            "canceled": False,
            "saved_path": str(chosen),
            "filename": Path(chosen).name
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dosya kopyalanamadı: {str(e)}")


@app.post("/api/save-blob-file")
async def save_blob_file(
    file: UploadFile = File(...),
    suggested_filename: str = Form("dosya")
):
    """Saves uploaded blob directly to user-chosen destination via native Windows Save As dialog."""
    ext = Path(suggested_filename).suffix or Path(file.filename or "").suffix
    chosen = await asyncio.to_thread(_open_native_save_dialog, suggested_filename, ext)
    if chosen == "CANCELED":
        return JSONResponse(content={"success": False, "canceled": True, "message": "Kaydetme iptal edildi."})
    if not chosen:
        return JSONResponse(content={"success": False, "canceled": False, "native_unsupported": True})

    try:
        with open(chosen, "wb") as f_out:
            shutil.copyfileobj(file.file, f_out)
        return JSONResponse(content={
            "success": True,
            "canceled": False,
            "saved_path": str(chosen),
            "filename": Path(chosen).name
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dosya yazılamadı: {str(e)}")


@app.get("/download-file/{task_id}")
async def download_file(task_id: str):
    """Returns the fully processed file for direct client download."""
    task = _download_tasks.get(task_id)
    if not task:
        return JSONResponse(status_code=404, content={"success": False, "message": "Task not found."})

    if task["status"] != "done":
        return JSONResponse(status_code=400, content={"success": False, "message": "File not ready yet."})

    filepath = task.get("filepath")
    if not filepath or not os.path.exists(filepath):
        return JSONResponse(status_code=404, content={"success": False, "message": "File not found."})

    ext = Path(filepath).suffix.lstrip(".")
    media_type = _guess_media_type(ext)

    response = FileResponse(
        path=filepath,
        filename=task["filename"],
        media_type=media_type,
    )
    return response


_AI_INSTALL_PROGRESS = {
    "status": "idle",
    "progress": 0,
    "current_model": "",
    "error": None
}


def check_ai_models_status() -> dict:
    """Checks the status and presence of local AI model weights."""
    models = {
        "realesrgan_general": {
            "name": "Real-ESRGAN (General 4x)",
            "installed": False,
            "size_mb": 67.0,
            "path": str(BASE_DIR / "RealESRGAN_x4plus.pth"),
        },
        "realesrgan_anime": {
            "name": "Real-ESRGAN (Anime 4x)",
            "installed": False,
            "size_mb": 17.9,
            "path": str(BASE_DIR / "RealESRGAN_x4plus_anime_6B.pth"),
        },
        "lama": {
            "name": "LaMa Magic Eraser",
            "installed": False,
            "size_mb": 198.0,
            "path": "",
        },
        "u2net": {
            "name": "U2-Net Background Remover",
            "installed": False,
            "size_mb": 176.0,
            "path": str(Path.home() / ".u2net" / "u2net.onnx"),
        },
    }

    p_gen = BASE_DIR / "RealESRGAN_x4plus.pth"
    if p_gen.exists() and p_gen.stat().st_size > 60 * 1024 * 1024:
        models["realesrgan_general"]["installed"] = True

    p_ani = BASE_DIR / "RealESRGAN_x4plus_anime_6B.pth"
    if p_ani.exists() and p_ani.stat().st_size > 15 * 1024 * 1024:
        models["realesrgan_anime"]["installed"] = True

    torch_checkpoints = Path.home() / ".cache" / "torch" / "hub" / "checkpoints"
    p_lama = torch_checkpoints / "big-lama.pt"
    if p_lama.exists() and p_lama.stat().st_size > 180 * 1024 * 1024:
        models["lama"]["installed"] = True
        models["lama"]["path"] = str(p_lama)
    else:
        alt_lama = Path.home() / ".cache" / "torch" / "hub" / "smartyagy_simple-lama-inpainting_main"
        if alt_lama.exists():
            models["lama"]["installed"] = True

    p_u2 = Path.home() / ".u2net" / "u2net.onnx"
    if p_u2.exists() and p_u2.stat().st_size > 160 * 1024 * 1024:
        models["u2net"]["installed"] = True

    all_installed = all(m["installed"] for m in models.values())
    essential_installed = (
        models["realesrgan_general"]["installed"]
        and models["u2net"]["installed"]
        and models["lama"]["installed"]
    )

    return {
        "success": True,
        "models": models,
        "all_installed": all_installed,
        "essential_installed": essential_installed,
        "torch_cuda_available": bool(torch.cuda.is_available()) if torch else False,
    }


def _run_pip_step(args: list, step_label: str, pct: int):
    """Executes a pip command safely with extended timeout and live progress reporting."""
    global _AI_INSTALL_PROGRESS
    _AI_INSTALL_PROGRESS["current_model"] = step_label
    _AI_INSTALL_PROGRESS["progress"] = pct
    py_exe = sys.executable
    cmd = [py_exe, "-m", "pip"] + args + [
        "--no-input",
        "--no-warn-script-location",
        "--prefer-binary",
        "--default-timeout", "180",
        "--retries", "5"
    ]
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        try:
            out, err = proc.communicate(timeout=900)
            if proc.returncode != 0:
                logger.warning(f"Pip command warning ({step_label}): {err[:300] if err else ''}")
        except subprocess.TimeoutExpired:
            proc.kill()
            logger.error(f"Pip command timed out: {step_label}")
    except Exception as ex:
        logger.warning(f"Pip execution error ({step_label}): {ex}")


def _download_chunked_file(url: str, dest_path: Path, expected_min_size: int, pct_start: int, pct_end: int, label: str):
    """Downloads large model weights in chunks with auto-resume (HTTP Range) and retry resilience against timeouts."""
    global _AI_INSTALL_PROGRESS
    tmp_path = dest_path.with_suffix(dest_path.suffix + ".tmp")

    max_retries = 5
    retry_delay = 2.0
    chunk_size = 256 * 1024  # 256 KB chunks for smoother updates and faster recovery
    total_size = 0

    for attempt in range(1, max_retries + 1):
        try:
            downloaded = tmp_path.stat().st_size if tmp_path.exists() else 0

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }

            if downloaded > 0:
                headers["Range"] = f"bytes={downloaded}-"

            req = urllib.request.Request(url, headers=headers)

            with _safe_urlopen(req, timeout=180) as resp:
                status_code = getattr(resp, "status", 200)
                content_len = resp.headers.get("Content-Length")
                content_range = resp.headers.get("Content-Range")

                if status_code == 206:
                    # Partial content: server accepted byte range
                    if content_range and "/" in content_range:
                        try:
                            range_total = int(content_range.split("/")[-1])
                            if range_total > 0:
                                total_size = range_total
                        except Exception:
                            pass
                    if total_size == 0 and content_len and content_len.isdigit():
                        total_size = downloaded + int(content_len)
                    file_mode = "ab"
                else:
                    # 200 OK: server sent full file or range unsupported
                    if content_len and content_len.isdigit():
                        total_size = int(content_len)
                    downloaded = 0
                    file_mode = "wb"

                total_mb = total_size / (1024 * 1024) if total_size > 0 else 0

                with open(tmp_path, file_mode) as f:
                    while True:
                        try:
                            chunk = resp.read(chunk_size)
                        except (socket.timeout, TimeoutError, ssl.SSLError) as read_err:
                            logger.warning(f"Chunk read timeout on {label} at {downloaded / (1024 * 1024):.1f} MB: {read_err}")
                            raise read_err

                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        dl_mb = downloaded / (1024 * 1024)

                        if total_size > 0:
                            ratio = min(1.0, downloaded / total_size)
                            curr_pct = int(pct_start + ratio * (pct_end - pct_start))
                            _AI_INSTALL_PROGRESS["current_model"] = f"{label} ({dl_mb:.1f} / {total_mb:.1f} MB - %{int(ratio * 100)})"
                            _AI_INSTALL_PROGRESS["progress"] = min(99, max(pct_start, curr_pct))
                        else:
                            _AI_INSTALL_PROGRESS["current_model"] = f"{label} ({dl_mb:.1f} MB indirildi...)"

            # Successful stream completion
            actual_size = tmp_path.stat().st_size if tmp_path.exists() else 0
            if actual_size >= expected_min_size:
                tmp_path.replace(dest_path)
                logger.info(f"Successfully downloaded and verified {label} ({actual_size} bytes).")
                return
            else:
                logger.warning(f"{label} indirilen boyut yetersiz ({actual_size} < {expected_min_size}). Yeniden deneniyor...")
                if attempt == max_retries:
                    raise RuntimeError(f"{label} indirmesi eksik ({actual_size} bytes, beklenen: {expected_min_size}).")

        except Exception as ex:
            err_msg = str(ex)
            is_network_err = (
                isinstance(ex, (socket.timeout, TimeoutError, urllib.error.URLError, ssl.SSLError))
                or "timed out" in err_msg.lower()
                or "timeout" in err_msg.lower()
                or "incomplete" in err_msg.lower()
                or "connection" in err_msg.lower()
            )
            if is_network_err and attempt < max_retries:
                dl_mb = (tmp_path.stat().st_size / (1024 * 1024)) if tmp_path.exists() else 0
                logger.warning(f"{label} bağlantı zaman aşımı/kesintisi ({ex}). {retry_delay:.1f}s sonra kaldığı yerden ({dl_mb:.1f} MB) devam edilecek (Deneme {attempt}/{max_retries})...")
                _AI_INSTALL_PROGRESS["current_model"] = f"{label} - Bağlantı tazeleniyor (Kaldığı yerden: {dl_mb:.1f} MB, Deneme {attempt}/{max_retries})..."
                time.sleep(retry_delay)
                retry_delay = min(10.0, retry_delay * 1.5)
                continue
            elif attempt >= max_retries:
                if tmp_path.exists():
                    try:
                        tmp_path.unlink()
                    except Exception:
                        pass
                raise RuntimeError(f"{label} indirilirken bağlantı zaman aşımına uğradı (5 deneme başarısız): {ex}") from ex
            else:
                raise ex


def _download_ai_models_worker():
    global _AI_INSTALL_PROGRESS, RealESRGANer, SimpleLama, LAMA_AVAILABLE, rembg_remove, REMBG_AVAILABLE, torch, cv2, np, RRDBNet
    _AI_INSTALL_PROGRESS["status"] = "downloading"
    _AI_INSTALL_PROGRESS["error"] = None

    try:
        # 1. Check and install python AI libraries if missing
        if torch is None or RealESRGANer is None or not REMBG_AVAILABLE:
            _run_pip_step(["install", "torch", "torchvision", "--index-url", "https://download.pytorch.org/whl/cpu"], "PyTorch CPU kuruluyor (~250 MB, 1-3 dk)...", 5)
            _run_pip_step(["install", "basicsr", "--no-deps"], "BasicSR mimarisi kuruluyor...", 15)
            _run_pip_step(["install", "realesrgan", "rembg", "simple-lama-inpainting", "faster-whisper", "demucs"], "AI yardımcı kütüphaneleri kuruluyor...", 22)

            # Dynamic re-import after installation
            ensure_ai_runtime()

        # 2. RealESRGAN General Model (~67 MB)
        gen_path = BASE_DIR / "RealESRGAN_x4plus.pth"
        if not gen_path.exists() or gen_path.stat().st_size < 60 * 1024 * 1024:
            url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"
            _download_chunked_file(url, gen_path, 60 * 1024 * 1024, 28, 48, "Real-ESRGAN General")
        else:
            _AI_INSTALL_PROGRESS["progress"] = max(_AI_INSTALL_PROGRESS["progress"], 48)

        # 3. RealESRGAN Anime Model (~18 MB)
        ani_path = BASE_DIR / "RealESRGAN_x4plus_anime_6B.pth"
        if not ani_path.exists() or ani_path.stat().st_size < 15 * 1024 * 1024:
            url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth"
            _download_chunked_file(url, ani_path, 15 * 1024 * 1024, 48, 62, "Real-ESRGAN Anime")
        else:
            _AI_INSTALL_PROGRESS["progress"] = max(_AI_INSTALL_PROGRESS["progress"], 62)

        # 4. LaMa Inpainting Model (~208 MB)
        lama_dir = Path.home() / ".cache" / "torch" / "hub" / "checkpoints"
        lama_dir.mkdir(parents=True, exist_ok=True)
        lama_path = lama_dir / "big-lama.pt"
        if not lama_path.exists() or lama_path.stat().st_size < 180 * 1024 * 1024:
            url = "https://github.com/enesmsahin/simple-lama-inpainting/releases/download/v0.1.0/big-lama.pt"
            _download_chunked_file(url, lama_path, 180 * 1024 * 1024, 62, 82, "LaMa Nesne Silici")
        else:
            _AI_INSTALL_PROGRESS["progress"] = max(_AI_INSTALL_PROGRESS["progress"], 82)

        # 5. U2-Net Background Remover Model (~176 MB)
        u2_dir = Path.home() / ".u2net"
        u2_dir.mkdir(parents=True, exist_ok=True)
        u2_path = u2_dir / "u2net.onnx"
        if not u2_path.exists() or u2_path.stat().st_size < 160 * 1024 * 1024:
            url = "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx"
            _download_chunked_file(url, u2_path, 160 * 1024 * 1024, 82, 98, "U2-Net Arka Plan")
        else:
            _AI_INSTALL_PROGRESS["progress"] = max(_AI_INSTALL_PROGRESS["progress"], 98)

        ensure_ai_runtime()
        _AI_INSTALL_PROGRESS["progress"] = 100
        _AI_INSTALL_PROGRESS["status"] = "done"
        _AI_INSTALL_PROGRESS["current_model"] = "Tüm Yapay Zekâ Modelleri Hazır!"
    except Exception as e:
        logger.error(f"AI model download failed: {e}")
        _AI_INSTALL_PROGRESS["status"] = "error"
        _AI_INSTALL_PROGRESS["error"] = str(e)


@app.get("/api/ai-status")
async def get_ai_status():
    """Returns local AI model presence and installation status."""
    st = check_ai_models_status()
    st["install_progress"] = _AI_INSTALL_PROGRESS
    return JSONResponse(content=st)


@app.post("/api/install-ai-models")
async def start_install_ai_models():
    """Starts background download of all required AI models."""
    global _AI_INSTALL_PROGRESS
    if _AI_INSTALL_PROGRESS["status"] == "downloading":
        return JSONResponse(content={"success": True, "message": "Zaten indiriliyor."})

    _AI_INSTALL_PROGRESS = {
        "status": "downloading",
        "progress": 5,
        "current_model": "Hazırlanıyor...",
        "error": None
    }
    asyncio.get_event_loop().run_in_executor(None, _download_ai_models_worker)
    return JSONResponse(content={"success": True, "message": "Model indirmesi başlatıldı."})


@app.post("/api/delete-ai-models")
async def delete_ai_models():
    """Deletes all local AI model weights from disk to free up disk space and flushes RAM/VRAM."""
    global _UPSCALER_INSTANCE, _UPSCALER_INSTANCES, _LAMA_INSTANCE
    
    # 1. Clear memory & VRAM
    try:
        _UPSCALER_INSTANCES.clear()
        _UPSCALER_INSTANCE = None
    except Exception:
        pass

    try:
        _LAMA_INSTANCE = None
    except Exception:
        pass

    if torch and torch.cuda.is_available():
        try:
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
        except Exception:
            pass
    gc.collect()

    freed_bytes = 0
    deleted_files = []

    # Paths to remove
    target_paths = [
        BASE_DIR / "RealESRGAN_x4plus.pth",
        BASE_DIR / "RealESRGAN_x4plus_anime_6B.pth",
        BASE_DIR / "RealESRGAN_x4plus.pth.tmp",
        BASE_DIR / "RealESRGAN_x4plus_anime_6B.pth.tmp",
        Path.home() / ".cache" / "torch" / "hub" / "checkpoints" / "big-lama.pt",
        Path.home() / ".u2net" / "u2net.onnx",
        Path.home() / ".u2net" / "u2net.onnx.tmp",
    ]

    for p in target_paths:
        if p.exists():
            try:
                size = p.stat().st_size
                p.unlink()
                freed_bytes += size
                deleted_files.append(p.name)
            except Exception as e:
                logger.error(f"Failed to delete {p}: {e}")

    freed_mb = round(freed_bytes / (1024 * 1024), 1)
    logger.info(f"Deleted local AI models. Freed {freed_mb} MB.")

    return JSONResponse(content={
        "success": True,
        "freed_mb": freed_mb,
        "deleted_files": deleted_files,
        "message": f"Yapay zeka modelleri silindi. {freed_mb} MB disk alanı açıldı."
    })



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
        "tiff": "image/tiff", "ico": "image/x-icon",
        "mp4": "video/mp4", "avi": "video/x-msvideo", "mkv": "video/x-matroska",
        "mov": "video/quicktime", "webm": "video/webm",
        "mp3": "audio/mpeg", "wav": "audio/wav", "ogg": "audio/ogg",
        "flac": "audio/flac", "aac": "audio/aac", "m4a": "audio/mp4",
    }
    return mapping.get(ext, "application/octet-stream")


@app.post("/encrypt-file")
async def encrypt_file(
    files: List[UploadFile] = File(...),
    password: str = Form(...),
    background_tasks: BackgroundTasks = None,
    x_task_id: str = Header(None)
):
    """Encrypts files or archives them into a secure AES-256 encrypted payload."""
    update_progress(x_task_id, 20, "Processing and Encrypting data...")
    
    uid = uuid.uuid4().hex[:8]
    
    if len(files) == 1:
        file = files[0]
        safe_name = _safe_filename(file.filename)
        src_path = UPLOAD_DIR / f"enc_{uid}_{safe_name}"
        with open(src_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        out_name = f"{safe_name}.enc"
    else:
        import zipfile
        safe_name = "vault_archive.zip"
        src_path = UPLOAD_DIR / f"enc_{uid}_{safe_name}"
        update_progress(x_task_id, 30, "Converting folder/multi-files to zip...")
        with zipfile.ZipFile(src_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in files:
                arcname = f.filename.lstrip("/\\")
                zf.writestr(arcname, f.file.read())
        out_name = f"{safe_name}.enc"
        
    out_path = DOWNLOAD_DIR / out_name
    
    try:
        update_progress(x_task_id, 50, "Encrypting file (This may take a while)...")
        bufferSize = 64 * 1024
        
        def do_encrypt():
            pyAesCrypt.encryptFile(str(src_path), str(out_path), password, bufferSize)

        await asyncio.to_thread(do_encrypt)
        
        update_progress(x_task_id, 90, "Packaging results...")
        if background_tasks:
            background_tasks.add_task(cleanup_files_and_memory, src_path, out_path)
        else:
            cleanup_files_and_memory(src_path)
            
        update_progress(x_task_id, 100, "Completed!")
        return FileResponse(
            path=str(out_path),
            filename=out_name,
            media_type="application/octet-stream",
        )
    except Exception as exc:
        cleanup_files_and_memory(src_path, out_path)
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Encryption error: {str(exc)}"},
        )

@app.post("/decrypt-file")
async def decrypt_file(
    file: UploadFile = File(...),
    password: str = Form(...),
    background_tasks: BackgroundTasks = None,
    x_task_id: str = Header(None)
):
    """Decrypts an AES-256 encrypted payload and restores original files."""
    update_progress(x_task_id, 20, "File uploaded, initializing decryption...")
    
    uid = uuid.uuid4().hex[:8]
    safe_name = _safe_filename(file.filename)
    
    src_path = UPLOAD_DIR / f"dec_{uid}_{safe_name}"
    with open(src_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    if safe_name.endswith(".enc"):
        out_name = safe_name[:-4]
    else:
        out_name = f"decrypted_{safe_name}"
        
    out_path = DOWNLOAD_DIR / out_name
    
    try:
        update_progress(x_task_id, 50, "Decrypting (This may take a while)...")
        bufferSize = 64 * 1024
        
        def do_decrypt():
            pyAesCrypt.decryptFile(str(src_path), str(out_path), password, bufferSize)

        await asyncio.to_thread(do_decrypt)
        
        update_progress(x_task_id, 90, "Packaging results...")
        if background_tasks:
            background_tasks.add_task(cleanup_files_and_memory, src_path, out_path)
        else:
            cleanup_files_and_memory(src_path)
            
        update_progress(x_task_id, 100, "Completed!")
        
        ext = Path(out_name).suffix.lstrip(".")
        media_type = _guess_media_type(ext)
        
        return FileResponse(
            path=str(out_path),
            filename=out_name,
            media_type=media_type,
        )
    except ValueError:
        cleanup_files_and_memory(src_path, out_path)
        raise HTTPException(status_code=400, detail="Incorrect password or corrupted file!")
    except Exception as exc:
        cleanup_files_and_memory(src_path, out_path)
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Decryption failed: {str(exc)}"},
        )

@app.get("/check-update")
async def check_update():
    """Checks for available over-the-air updates."""
    return JSONResponse(content={"status": "ready", "message": "Checking for updates..."})

@app.post("/apply-update")
async def apply_update(x_task_id: str = Header(None)):
    """Downloads and applies updates from the source repository securely."""
    update_progress(x_task_id, 10, "Connecting to GitHub...")
    
    zip_path = DOWNLOAD_DIR / "update.zip"
    extract_path = DOWNLOAD_DIR / "update_tmp"
    
    try:
        update_progress(x_task_id, 30, "Downloading new updates...")
        def _download():
            urllib.request.urlretrieve(GITHUB_REPO_URL, str(zip_path))
        await asyncio.to_thread(_download)
        
        update_progress(x_task_id, 60, "Applying system updates...")
        def _extract_and_apply():
            if extract_path.exists():
                shutil.rmtree(extract_path)
            extract_path.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            
            extracted_items = list(extract_path.iterdir())
            if not extracted_items:
                raise Exception("Downloaded ZIP file is empty.")
            
            root_dir = extracted_items[0] if extracted_items[0].is_dir() else extract_path
            
            allowed_exts = {".py", ".html", ".js", ".css"}
            protected_folders = {"venv", "uploads", "downloads", ".git", ".env"}
            
            for item in root_dir.rglob("*"):
                if item.is_file():
                    rel_path = item.relative_to(root_dir)
                    
                    is_protected = False
                    for part in rel_path.parts:
                        if part in protected_folders:
                            is_protected = True
                            break
                    if is_protected:
                        continue
                        
                    if item.suffix.lower() in allowed_exts:
                        target = BASE_DIR / rel_path
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(item, target)
                        
            if zip_path.exists():
                zip_path.unlink()
            if extract_path.exists():
                shutil.rmtree(extract_path)
                
        await asyncio.to_thread(_extract_and_apply)
        
        update_progress(x_task_id, 100, "Update Completed!")
        return JSONResponse(content={
            "status": "success", 
            "message": "G-Toolbox has been updated successfully! Please restart the server."
        })
        
    except Exception as e:
        logger.error(f"Update failed: {e}")
        if zip_path.exists():
            zip_path.unlink()
        if extract_path.exists():
            shutil.rmtree(extract_path, ignore_errors=True)
        return JSONResponse(status_code=500, content={"status": "error", "message": f"Update failed: {str(e)}"})

@app.post("/update-ytdlp")
async def update_ytdlp():
    """Updates yt-dlp to the latest version to prevent YouTube streaming download breakages."""
    def _run_update():
        try:
            cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
            v_proc = subprocess.run([sys.executable, "-m", "yt_dlp", "--version"], capture_output=True, text=True, timeout=10)
            ver = v_proc.stdout.strip() if v_proc.returncode == 0 else "Latest"
            return {"success": True, "version": ver, "message": f"yt-dlp engine successfully updated to {ver}."}
        except Exception as e:
            return {"success": False, "message": f"Update failed: {str(e)}"}

    res = await asyncio.to_thread(_run_update)
    code = 200 if res.get("success") else 500
    return JSONResponse(status_code=code, content=res)


# ── Demucs Audio Stem Separation ──────────────────────────────────
@app.post("/separate-audio")
async def separate_audio(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    stems: str = Form("vocals"),
    x_task_id: str = Header(None, alias="X-Task-ID")
):
    """Separates audio into vocals and instrumental (or 4 stems) using Demucs."""
    ensure_ai_runtime()
    update_progress(x_task_id, 5, "Audio uploaded. Initializing Demucs AI...")
    safe_name = _safe_filename(file.filename)
    input_path = UPLOAD_DIR / f"{uuid.uuid4().hex}_{safe_name}"
    
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    out_folder = DOWNLOAD_DIR / f"separated_{uuid.uuid4().hex}"
    out_folder.mkdir(parents=True, exist_ok=True)

    def _process():
        try:
            update_progress(x_task_id, 25, "Separating audio stems with Demucs neural network...")
            demucs_opts = [
                "-n", "htdemucs",
                "--out", str(out_folder)
            ]
            if stems == "vocals":
                demucs_opts.extend(["--two-stems", "vocals"])
            demucs_opts.append(str(input_path))

            # Try in-process execution first to support PyInstaller frozen desktop apps
            in_process_success = False
            try:
                import demucs.separate
                demucs.separate.main(demucs_opts)
                in_process_success = True
            except Exception as in_err:
                logger.warning(f"In-process Demucs encountered notice: {in_err}. Checking subprocess...")

            if not in_process_success:
                py_exe = sys.executable
                if getattr(sys, "frozen", False):
                    py_exe = shutil.which("python") or shutil.which("python3") or sys.executable
                cmd = [py_exe, "-m", "demucs"] + demucs_opts
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                if proc.returncode != 0:
                    raise RuntimeError(f"Demucs processing error: {proc.stderr or proc.stdout}")

            update_progress(x_task_id, 80, "Compressing separated audio stems into ZIP...")
            track_dirs = list((out_folder / "htdemucs").glob("*"))
            if not track_dirs:
                raise RuntimeError("No output stems produced by Demucs.")
            
            target_track_dir = track_dirs[0]
            zip_filename = f"{Path(safe_name).stem}_separated_stems.zip"
            zip_path = DOWNLOAD_DIR / zip_filename
            
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for stem_file in target_track_dir.glob("*.wav"):
                    zf.write(stem_file, arcname=stem_file.name)

            update_progress(x_task_id, 100, "Audio separation complete!")
            return zip_path
        finally:
            cleanup_files_and_memory(input_path)
            shutil.rmtree(out_folder, ignore_errors=True)

    try:
        zip_path = await asyncio.to_thread(_process)
        background_tasks.add_task(cleanup_files_and_memory, zip_path)
        return FileResponse(
            zip_path,
            media_type="application/zip",
            filename=zip_path.name
        )
    except Exception as e:
        logger.error(f"Demucs separation failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


# ── Faster-Whisper Local Transcription ────────────────────────────
_WHISPER_MODELS: dict[str, object] = {}

def get_whisper_model(model_size: str = "base"):
    global _WHISPER_MODELS
    ensure_ai_runtime()
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise RuntimeError("faster-whisper library is not installed.")
    
    key = str(model_size).lower().strip() or "base"
    if key not in _WHISPER_MODELS:
        device = "cuda" if (torch and torch.cuda.is_available()) else "cpu"
        compute_type = "float16" if (torch and torch.cuda.is_available()) else "int8"
        _WHISPER_MODELS[key] = WhisperModel(key, device=device, compute_type=compute_type)
    return _WHISPER_MODELS[key]

def format_timestamp(seconds: float) -> str:
    """Formats float seconds into SRT timestamp HH:MM:SS,mmm."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    msecs = int(round((seconds - int(seconds)) * 1000))
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{msecs:03d}"

@app.post("/transcribe-media")
async def transcribe_media(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    output_format: str = Form("txt"),
    language: str = Form("auto"),
    model_size: str = Form("base"),
    x_task_id: str = Header(None, alias="X-Task-ID")
):
    """Generates transcripts and subtitles from video or audio files using Faster-Whisper."""
    ensure_ai_runtime()
    update_progress(x_task_id, 10, "Loading audio and initializing Faster-Whisper model...")
    safe_name = _safe_filename(file.filename)
    input_path = UPLOAD_DIR / f"{uuid.uuid4().hex}_{safe_name}"

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    def _transcribe():
        try:
            update_progress(x_task_id, 30, "Transcribing speech to text...")
            model = get_whisper_model(model_size=model_size)
            lang_param = None if language.lower() in ["auto", ""] else language.lower()

            segments, info = model.transcribe(str(input_path), language=lang_param, beam_size=5)
            update_progress(x_task_id, 75, f"Transcription completed ({info.language.upper()}, {info.duration:.1f}s). Formatting...")

            text_lines = []
            srt_entries = []
            raw_segments = []

            for i, seg in enumerate(segments, start=1):
                clean_text = seg.text.strip()
                text_lines.append(clean_text)
                srt_entries.append(
                    f"{i}\n{format_timestamp(seg.start)} --> {format_timestamp(seg.end)}\n{clean_text}\n"
                )
                raw_segments.append({
                    "id": i,
                    "start": seg.start,
                    "end": seg.end,
                    "text": clean_text
                })

            base_stem = Path(safe_name).stem
            if output_format == "srt":
                out_path = DOWNLOAD_DIR / f"{base_stem}_subtitles.srt"
                out_path.write_text("\n".join(srt_entries), encoding="utf-8")
                media_type = "text/plain"
            elif output_format == "json":
                return {
                    "language": info.language,
                    "duration": info.duration,
                    "full_text": "\n".join(text_lines),
                    "segments": raw_segments
                }
            else:
                out_path = DOWNLOAD_DIR / f"{base_stem}_transcript.txt"
                out_path.write_text("\n\n".join(text_lines), encoding="utf-8")
                media_type = "text/plain"

            update_progress(x_task_id, 100, "Transcription finished!")
            return out_path, media_type
        finally:
            cleanup_files_and_memory(input_path)

    try:
        res = await asyncio.to_thread(_transcribe)
        if isinstance(res, dict):
            return JSONResponse(res)
        out_path, media_type = res
        background_tasks.add_task(cleanup_files_and_memory, out_path)
        return FileResponse(out_path, media_type=media_type, filename=out_path.name)
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


# ── EXIF & Metadata Inspector / Stripper ──────────────────────────
@app.post("/view-metadata")
async def view_metadata(file: UploadFile = File(...)):
    """Extracts and inspects EXIF metadata tags including GPS coordinates from an image."""
    try:
        image = Image.open(file.file)
        exif_data = image.getexif()
        metadata = {}
        if exif_data:
            for tag_id, value in exif_data.items():
                tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                if isinstance(value, bytes):
                    metadata[tag_name] = f"<binary data: {len(value)} bytes>"
                else:
                    metadata[tag_name] = str(value)

            # Extract GPSInfo sub-IFD (Pillow 10+)
            try:
                gps_ifd = exif_data.get_ifd(ExifTags.IFD.GPSInfo)
                if gps_ifd:
                    for gps_id, val in gps_ifd.items():
                        gps_tag_name = ExifTags.GPSTAGS.get(gps_id, f"GPS_{gps_id}")
                        if isinstance(val, bytes):
                            metadata[f"GPS.{gps_tag_name}"] = f"<binary: {len(val)} bytes>"
                        else:
                            metadata[f"GPS.{gps_tag_name}"] = str(val)
            except Exception:
                pass

        return JSONResponse({
            "filename": file.filename,
            "format": image.format,
            "size": f"{image.width}x{image.height}",
            "tag_count": len(metadata),
            "tags": metadata
        })
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"Failed to read image metadata: {str(e)}"})

@app.post("/strip-metadata")
async def strip_metadata(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Completely strips EXIF, GPS, camera model, and private metadata from an image."""
    safe_name = _safe_filename(file.filename)
    dest_path = DOWNLOAD_DIR / f"clean_{uuid.uuid4().hex}_{safe_name}"
    try:
        image = Image.open(file.file)
        try:
            from PIL import ImageOps
            image = ImageOps.exif_transpose(image)
        except Exception:
            pass

        # Recreate image purely without metadata tags
        clean_img = Image.new(image.mode, image.size)
        clean_img.paste(image)

        fmt = image.format or "PNG"
        if fmt.upper() in ("JPG", "JPEG"):
            if clean_img.mode not in ("RGB", "L"):
                clean_img = clean_img.convert("RGB")

        clean_img.save(dest_path, format=fmt)

        background_tasks.add_task(cleanup_files_and_memory, dest_path)
        return FileResponse(
            dest_path,
            media_type=f"image/{fmt.lower()}",
            filename=f"clean_{safe_name}"
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": f"Strip failed: {str(e)}"})


# ── Video to GIF / WebP Animation ────────────────────────────────
@app.post("/video-to-anim")
async def video_to_anim(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    start_time: str = Form("00:00:00"),
    duration: float = Form(5.0),
    fps: int = Form(15),
    width: int = Form(480),
    anim_format: str = Form("gif"),
    quality: int = Form(80),
    x_task_id: str = Header(None, alias="X-Task-ID")
):
    """Converts a specific segment of a video to optimized animated GIF or WebP."""
    update_progress(x_task_id, 10, "Uploading video for animation render...")
    safe_name = _safe_filename(file.filename)
    input_path = UPLOAD_DIR / f"{uuid.uuid4().hex}_{safe_name}"
    
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    out_ext = "webp" if anim_format.lower() == "webp" else "gif"
    out_path = DOWNLOAD_DIR / f"{Path(safe_name).stem}_anim_{uuid.uuid4().hex[:6]}.{out_ext}"

    def _render():
        try:
            update_progress(x_task_id, 40, f"Rendering high-quality animated {out_ext.upper()} via FFmpeg...")
            ffmpeg_exe = "ffmpeg"
            if FFMPEG_DIR:
                custom_path = Path(FFMPEG_DIR) / "ffmpeg.exe"
                if custom_path.exists():
                    ffmpeg_exe = str(custom_path)

            if out_ext == "gif":
                vf = f"fps={fps},scale={width}:-2:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"
                cmd = [
                    ffmpeg_exe, "-y",
                    "-ss", str(start_time),
                    "-t", str(duration),
                    "-i", str(input_path),
                    "-vf", vf,
                    str(out_path)
                ]
            else:
                vf = f"fps={fps},scale={width}:-2:flags=lanczos"
                cmd = [
                    ffmpeg_exe, "-y",
                    "-ss", str(start_time),
                    "-t", str(duration),
                    "-i", str(input_path),
                    "-vf", vf,
                    "-vcodec", "libwebp",
                    "-lossless", "0",
                    "-q:v", str(quality),
                    "-loop", "0",
                    "-an",
                    str(out_path)
                ]

            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            if proc.returncode != 0:
                raise RuntimeError(f"FFmpeg error: {proc.stderr or proc.stdout}")

            update_progress(x_task_id, 100, f"Rendered {out_ext.upper()} successfully!")
            return out_path
        finally:
            cleanup_files_and_memory(input_path)

    try:
        rendered_file = await asyncio.to_thread(_render)
        background_tasks.add_task(cleanup_files_and_memory, rendered_file)
        media_type = "image/webp" if out_ext == "webp" else "image/gif"
        return FileResponse(rendered_file, media_type=media_type, filename=rendered_file.name)
    except Exception as e:
        logger.error(f"Animation conversion failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


# ── Hardware Telemetry & VRAM Management ─────────────────────────
def purge_vram_and_models():
    """Unloads cached AI models (RealESRGAN, LaMa, Faster-Whisper) and purges CUDA/RAM cache."""
    global _UPSCALER_INSTANCE, _UPSCALER_INSTANCES, _LAMA_INSTANCE, _WHISPER_MODELS
    _UPSCALER_INSTANCE = None
    _UPSCALER_INSTANCES.clear()
    _LAMA_INSTANCE = None
    _WHISPER_MODELS.clear()
    
    import gc
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
    except Exception:
        pass
    logger.info("🧹 Purged all cached AI models and released VRAM/RAM.")

@app.get("/api/system-status")
async def get_system_status():
    """Returns GPU VRAM and CPU RAM telemetry."""
    import psutil
    ram = psutil.virtual_memory()
    res = {
        "cpu_ram_total_mb": round(ram.total / (1024 * 1024), 1),
        "cpu_ram_used_mb": round(ram.used / (1024 * 1024), 1),
        "cpu_ram_percent": ram.percent,
        "cuda_available": False,
        "gpu_name": "None",
        "vram_total_mb": 0,
        "vram_allocated_mb": 0,
        "vram_reserved_mb": 0,
        "models_cached": {
            "upscalers": len(_UPSCALER_INSTANCES),
            "lama": _LAMA_INSTANCE is not None,
            "whisper": len(_WHISPER_MODELS)
        }
    }
    try:
        import torch
        if torch.cuda.is_available():
            res["cuda_available"] = True
            res["gpu_name"] = torch.cuda.get_device_name(0)
            res["vram_total_mb"] = round(torch.cuda.get_device_properties(0).total_memory / (1024 * 1024), 1)
            res["vram_allocated_mb"] = round(torch.cuda.memory_allocated(0) / (1024 * 1024), 1)
            res["vram_reserved_mb"] = round(torch.cuda.memory_reserved(0) / (1024 * 1024), 1)
    except Exception:
        pass
    return JSONResponse(res)

@app.post("/api/purge-vram")
async def api_purge_vram():
    """Manually purges VRAM and unloads models."""
    purge_vram_and_models()
    status_response = await get_system_status()
    import json
    status_dict = json.loads(status_response.body.decode("utf-8"))
    return JSONResponse({"success": True, "message": "VRAM and AI models successfully unloaded.", "status": status_dict})


# ── Video Hardsub Burner ──────────────────────────────────────────
@app.post("/burn-subtitles")
async def burn_subtitles(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    subtitle: UploadFile = File(...),
    font_size: int = Form(22),
    font_color: str = Form("white"),
    x_task_id: str = Header(None, alias="X-Task-ID")
):
    """Burns SRT subtitles permanently onto video using FFmpeg."""
    update_progress(x_task_id, 10, "Uploading video and subtitle files...")
    uid = uuid.uuid4().hex[:8]
    safe_video = _safe_filename(video.filename)
    safe_sub = _safe_filename(subtitle.filename)

    video_path = UPLOAD_DIR / f"v_{uid}_{safe_video}"
    sub_path = UPLOAD_DIR / f"s_{uid}_{safe_sub}"
    out_name = f"{Path(safe_video).stem}_subbed_{uid}.mp4"
    out_path = DOWNLOAD_DIR / out_name

    with open(video_path, "wb") as vb:
        shutil.copyfileobj(video.file, vb)
    with open(sub_path, "wb") as sb:
        shutil.copyfileobj(subtitle.file, sb)

    color_map = {
        "white": "&H00FFFFFF",
        "yellow": "&H0000FFFF",
        "cyan": "&H00FFFF00",
        "green": "&H0000FF00",
    }
    color_code = color_map.get(font_color.lower(), "&H00FFFFFF")

    def _burn():
        try:
            update_progress(x_task_id, 40, "Burning subtitles into video stream...")
            ffmpeg_exe = "ffmpeg"
            if FFMPEG_DIR:
                custom_path = Path(FFMPEG_DIR) / "ffmpeg.exe"
                if custom_path.exists():
                    ffmpeg_exe = str(custom_path)

            # Format subtitle path for FFmpeg filter on Windows
            sub_str = str(sub_path).replace("\\", "/").replace(":", "\\:")
            vf = f"subtitles='{sub_str}':force_style='FontSize={font_size},PrimaryColour={color_code},OutlineColour=&H00000000,BorderStyle=3,Outline=2'"

            cmd = [
                ffmpeg_exe, "-y",
                "-i", str(video_path),
                "-vf", vf,
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "22",
                "-c:a", "copy",
                str(out_path)
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if proc.returncode != 0:
                raise RuntimeError(f"Subtitle burn error: {proc.stderr or proc.stdout}")

            update_progress(x_task_id, 100, "Subtitles burned successfully!")
            return out_path
        finally:
            cleanup_files_and_memory(video_path, sub_path)

    try:
        res_file = await asyncio.to_thread(_burn)
        background_tasks.add_task(cleanup_files_and_memory, res_file)
        return FileResponse(res_file, media_type="video/mp4", filename=out_name)
    except Exception as e:
        logger.error(f"Subtitle burn failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


# ── PDF Swiss Army Toolkit ─────────────────────────────────────────
@app.post("/pdf-merge")
async def pdf_merge(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    x_task_id: str = Header(None, alias="X-Task-ID")
):
    """Merges multiple PDF files in order into a single unified document."""
    update_progress(x_task_id, 20, "Uploading PDF files for merge...")
    import pypdf
    uid = uuid.uuid4().hex[:8]
    out_name = f"merged_document_{uid}.pdf"
    out_path = DOWNLOAD_DIR / out_name

    saved_paths = []
    for f in files:
        p = UPLOAD_DIR / f"pdf_{uid}_{_safe_filename(f.filename)}"
        with open(p, "wb") as buf:
            shutil.copyfileobj(f.file, buf)
        saved_paths.append(p)

    def _do_merge():
        try:
            update_progress(x_task_id, 50, "Merging PDF pages...")
            merger = pypdf.PdfWriter()
            for sp in saved_paths:
                merger.append(str(sp))
            with open(out_path, "wb") as out_buf:
                merger.write(out_buf)
            merger.close()
            update_progress(x_task_id, 100, "PDFs merged successfully!")
            return out_path
        finally:
            cleanup_files_and_memory(*saved_paths)

    try:
        merged_file = await asyncio.to_thread(_do_merge)
        background_tasks.add_task(cleanup_files_and_memory, merged_file)
        return FileResponse(merged_file, media_type="application/pdf", filename=out_name)
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": f"Merge failed: {str(e)}"})


@app.post("/pdf-split")
async def pdf_split(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    page_range: Optional[str] = Form(None),
    page_ranges: Optional[str] = Form(None),
    x_task_id: str = Header(None, alias="X-Task-ID")
):
    """Extracts specified page ranges from a PDF."""
    target_range = page_ranges or page_range or "1-1"
    update_progress(x_task_id, 20, "Uploading PDF for extraction...")
    import pypdf
    uid = uuid.uuid4().hex[:8]
    safe_name = _safe_filename(file.filename)
    src_path = UPLOAD_DIR / f"split_{uid}_{safe_name}"
    out_name = f"{Path(safe_name).stem}_pages_{uid}.pdf"
    out_path = DOWNLOAD_DIR / out_name

    with open(src_path, "wb") as buf:
        shutil.copyfileobj(file.file, buf)

    def _do_split():
        try:
            update_progress(x_task_id, 50, f"Extracting pages ({target_range})...")
            reader = pypdf.PdfReader(str(src_path))
            writer = pypdf.PdfWriter()
            total_pages = len(reader.pages)

            pages_to_extract = set()
            parts = [p.strip() for p in target_range.split(",") if p.strip()]
            for part in parts:
                if "-" in part:
                    s_str, e_str = part.split("-", 1)
                    s_idx = max(1, int(s_str.strip()))
                    e_idx = min(total_pages, int(e_str.strip()))
                    for p_num in range(s_idx, e_idx + 1):
                        pages_to_extract.add(p_num - 1)
                else:
                    p_idx = int(part) - 1
                    if 0 <= p_idx < total_pages:
                        pages_to_extract.add(p_idx)

            if not pages_to_extract:
                raise ValueError("No valid pages selected.")

            for page_idx in sorted(pages_to_extract):
                writer.add_page(reader.pages[page_idx])

            with open(out_path, "wb") as out_buf:
                writer.write(out_buf)

            update_progress(x_task_id, 100, "Pages extracted successfully!")
            return out_path
        finally:
            cleanup_files_and_memory(src_path)

    try:
        split_file = await asyncio.to_thread(_do_split)
        background_tasks.add_task(cleanup_files_and_memory, split_file)
        return FileResponse(split_file, media_type="application/pdf", filename=out_name)
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": f"Split failed: {str(e)}"})


@app.post("/pdf-extract-text")
async def pdf_extract_text(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    x_task_id: str = Header(None, alias="X-Task-ID")
):
    """Extracts all readable text content from a PDF file."""
    update_progress(x_task_id, 20, "Uploading PDF for text extraction...")
    import pypdf
    uid = uuid.uuid4().hex[:8]
    safe_name = _safe_filename(file.filename)
    src_path = UPLOAD_DIR / f"txt_{uid}_{safe_name}"

    with open(src_path, "wb") as buf:
        shutil.copyfileobj(file.file, buf)

    def _do_extract():
        try:
            update_progress(x_task_id, 50, "Extracting text content...")
            reader = pypdf.PdfReader(str(src_path))
            full_text = []
            for i, page in enumerate(reader.pages, start=1):
                txt = page.extract_text() or ""
                full_text.append(f"--- PAGE {i} ---\n{txt.strip()}\n")

            update_progress(x_task_id, 100, "Text extracted successfully!")
            return {
                "success": True,
                "text": "\n".join(full_text),
                "pages": len(reader.pages)
            }
        finally:
            cleanup_files_and_memory(src_path)

    try:
        res = await asyncio.to_thread(_do_extract)
        return JSONResponse(content=res)
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": f"Extract failed: {str(e)}"})


# ── Audio Speed, Pitch & Effects Engine (Slowed+Reverb / Nightcore) ─
@app.post("/audio-effects")
async def audio_effects(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    preset: str = Form("custom"),
    tempo: float = Form(1.0),
    pitch: float = Form(1.0),
    reverb: Optional[str] = Form(None),
    add_reverb: bool = Form(False),
    x_task_id: str = Header(None, alias="X-Task-ID")
):
    """Applies speed, pitch, nightcore, and slowed+reverb effects to audio."""
    update_progress(x_task_id, 10, "Uploading audio for effects processing...")
    safe_name = _safe_filename(file.filename)
    uid = uuid.uuid4().hex[:8]
    input_path = UPLOAD_DIR / f"fx_{uid}_{safe_name}"
    out_name = f"{Path(safe_name).stem}_fx_{uid}.mp3"
    out_path = DOWNLOAD_DIR / out_name

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    enable_reverb = add_reverb or (str(reverb).lower() in ("true", "1", "yes"))

    def _apply_fx():
        try:
            update_progress(x_task_id, 40, f"Applying audio effects filter chain...")
            ffmpeg_exe = "ffmpeg"
            if FFMPEG_DIR:
                custom_path = Path(FFMPEG_DIR) / "ffmpeg.exe"
                if custom_path.exists():
                    ffmpeg_exe = str(custom_path)

            filters = []
            if preset == "slowed_reverb":
                filters.append("atempo=0.85,aecho=0.8:0.88:60:0.4")
            elif preset == "nightcore":
                filters.append("asetrate=44100*1.25,atempo=1.0")
            elif preset == "speed_1_5x":
                filters.append("atempo=1.5")
            elif preset == "slow_0_75x":
                filters.append("atempo=0.75")
            else:
                clamped_tempo = max(0.5, min(2.0, tempo))
                clamped_pitch = max(0.5, min(2.0, pitch))

                if abs(clamped_pitch - 1.0) > 0.01:
                    rate = int(44100 * clamped_pitch)
                    comp_tempo = clamped_tempo / clamped_pitch
                    # atempo requires between 0.5 and 2.0
                    comp_tempo = max(0.5, min(2.0, comp_tempo))
                    filters.append(f"asetrate={rate},atempo={comp_tempo:.3f}")
                else:
                    filters.append(f"atempo={clamped_tempo:.3f}")

                if enable_reverb:
                    filters.append("aecho=0.8:0.88:60:0.4")

            af = ",".join(filters) if filters else "atempo=1.0"

            cmd = [
                ffmpeg_exe, "-y",
                "-i", str(input_path),
                "-af", af,
                "-q:a", "2",
                str(out_path)
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if proc.returncode != 0:
                raise RuntimeError(f"Audio effect error: {proc.stderr or proc.stdout}")

            update_progress(x_task_id, 100, "Audio effects rendered successfully!")
            return out_path
        finally:
            cleanup_files_and_memory(input_path)

    try:
        rendered = await asyncio.to_thread(_apply_fx)
        background_tasks.add_task(cleanup_files_and_memory, rendered)
        return FileResponse(rendered, media_type="audio/mpeg", filename=out_name)
    except Exception as e:
        logger.error(f"Audio effects failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


# ── AI & Spectral Noise Suppressor ─────────────────────────────────
@app.post("/clean-audio-noise")
async def clean_audio_noise(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    noise_preset: Optional[str] = Form("medium"),
    noise_reduction_db: Optional[float] = Form(None),
    voice_focus: Optional[str] = Form(None),
    x_task_id: str = Header(None, alias="X-Task-ID")
):
    """Removes background hum, fan noise, and hiss using Adaptive FFT De-Noise."""
    update_progress(x_task_id, 10, "Uploading media for noise reduction...")
    safe_name = _safe_filename(file.filename)
    uid = uuid.uuid4().hex[:8]
    input_path = UPLOAD_DIR / f"dn_{uid}_{safe_name}"
    
    ext = Path(safe_name).suffix.lower().lstrip(".")
    is_video = ext in VIDEO_EXTENSIONS
    out_ext = ext if is_video else "mp3"
    out_name = f"{Path(safe_name).stem}_clean_{uid}.{out_ext}"
    out_path = DOWNLOAD_DIR / out_name

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Calculate filter string
    is_voice_focus = str(voice_focus).lower() in ("true", "1", "yes")
    if noise_reduction_db is not None:
        nr_val = -abs(float(noise_reduction_db))
        denoise_filter = f"afftdn=nf={nr_val}:tn=1"
    else:
        preset_filters = {
            "light": "afftdn=nf=-20:tn=1",
            "medium": "afftdn=nf=-30:tn=1",
            "heavy": "afftdn=nf=-42:tn=1",
            "voice_focus": "highpass=f=85,lowpass=f=3800,afftdn=nf=-30:tn=1",
        }
        denoise_filter = preset_filters.get(str(noise_preset).lower(), "afftdn=nf=-30:tn=1")

    if is_voice_focus and "highpass" not in denoise_filter:
        af = f"highpass=f=85,lowpass=f=3800,{denoise_filter}"
    else:
        af = denoise_filter

    def _denoise():
        try:
            update_progress(x_task_id, 40, f"Processing audio with FFT noise suppressor...")
            ffmpeg_exe = "ffmpeg"
            if FFMPEG_DIR:
                custom_path = Path(FFMPEG_DIR) / "ffmpeg.exe"
                if custom_path.exists():
                    ffmpeg_exe = str(custom_path)

            if is_video:
                cmd = [
                    ffmpeg_exe, "-y",
                    "-i", str(input_path),
                    "-c:v", "copy",
                    "-af", af,
                    "-c:a", "aac",
                    "-b:a", "192k",
                    str(out_path)
                ]
            else:
                cmd = [
                    ffmpeg_exe, "-y",
                    "-i", str(input_path),
                    "-af", af,
                    "-q:a", "2",
                    str(out_path)
                ]

            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
            if proc.returncode != 0:
                raise RuntimeError(f"Denoise error: {proc.stderr or proc.stdout}")

            update_progress(x_task_id, 100, "Audio noise cleaned successfully!")
            return out_path
        finally:
            cleanup_files_and_memory(input_path)

    try:
        cleaned = await asyncio.to_thread(_denoise)
        background_tasks.add_task(cleanup_files_and_memory, cleaned)
        media_type = _guess_media_type(out_ext)
        return FileResponse(cleaned, media_type=media_type, filename=out_name)
    except Exception as e:
        logger.error(f"Denoising failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
