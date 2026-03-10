"""
G-Toolbox — Multi-purpose Media/File Processing Toolbox
Backend: FastAPI + Jinja2 + Pillow + ffmpeg-python + rembg + yt-dlp
"""

import asyncio
import glob
import logging
import os
import re
import shutil
import subprocess
import uuid
import pyAesCrypt
from fastapi import HTTPException
from pathlib import Path

import ffmpeg
import yt_dlp
from PIL import Image
from rembg import remove as rembg_remove
from typing import List
import zipfile
import urllib.request

GITHUB_REPO_URL = "https://github.com/KULLANICI_ADIN/REPO_ADIN/archive/refs/heads/main.zip"

try:
    from simple_lama_inpainting import SimpleLama
    LAMA_AVAILABLE = True
except ImportError:
    LAMA_AVAILABLE = False

try:
    import cv2
    import numpy as np
    import torch
    
    # HOTFIX: basicsr requires torchvision.transforms.functional_tensor
    # which was removed in newer versions of torchvision.
    import sys
    try:
        import torchvision.transforms.functional_tensor
    except ImportError:
        import torchvision.transforms.functional as functional
        sys.modules['torchvision.transforms.functional_tensor'] = functional
    
    from basicsr.archs.rrdbnet_arch import RRDBNet
    from realesrgan import RealESRGANer
except ImportError as e:
    print(f"Warning: Image upscaling components could not be loaded. Reason: {e}")
    cv2 = None
    np = None
    torch = None
    RRDBNet = None
    RealESRGANer = None

def get_upscaler():
    if RealESRGANer is None:
        raise RuntimeError("realesrgan library or dependencies not installed.")

    import urllib.request
    model_name = "RealESRGAN_x4plus.pth"
    model_path = BASE_DIR / model_name
    model_url = f"https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/{model_name}"
    
    if not model_path.exists():
        logger.info(f"Downloading {model_name}...")
        urllib.request.urlretrieve(model_url, str(model_path))

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
    
    half = True if torch.cuda.is_available() else False

    upscaler_model = RealESRGANer(
        scale=4,
        model_path=str(model_path),
        model=model,
        tile=256,
        tile_pad=10,
        pre_pad=0,
        half=half,
        device=device
    )
    return upscaler_model

from fastapi import BackgroundTasks, FastAPI, File, Form, UploadFile, Request, Header
from fastapi.responses import FileResponse, JSONResponse
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

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
DOWNLOAD_DIR = BASE_DIR / "downloads"

UPLOAD_DIR.mkdir(exist_ok=True)
DOWNLOAD_DIR.mkdir(exist_ok=True)


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
    logger.info(f"✅ ffmpeg found: {FFMPEG_DIR}")
else:
    logger.warning(
        "⚠️ ffmpeg not found! Video download (merge/convert) may not work. "
        "Place ffmpeg.exe in the project directory or add it to PATH."
    )

app = FastAPI(title="G-Toolbox", version="4.0.0")

progress_store: dict[str, dict] = {}

def update_progress(task_id: str, progress: int, message: str):
    if task_id:
        progress_store[task_id] = {"progress": progress, "message": message}

@app.get("/progress/{task_id}")
async def get_progress(task_id: str):
    """Returns the current progress status for a given task ID."""
    return JSONResponse(content=progress_store.get(task_id, {"progress": 0, "message": ""}))

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

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

    try:
        update_progress(x_task_id, 50, "AI model is executing. This process relies on CPU and GPU overhead...")
        img = Image.open(src_path)
        result = rembg_remove(img)
        result.save(str(out_path), format="PNG")

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
    update_progress(x_task_id, 20, "File uploaded, initializing process...")
    if not LAMA_AVAILABLE:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "simple-lama-inpainting not installed or could not be initialized."}
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
            from simple_lama_inpainting import SimpleLama
            lama_model = SimpleLama()
            orig = Image.open(img_path)
            # Mask format needs to be grayscale (L) where white is inpaint area
            mask_img = Image.open(mask_path).convert("L") 
            result = lama_model(orig, mask_img)
            del lama_model
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
    background_tasks: BackgroundTasks = None,
    x_task_id: str = Header(None)
):
    update_progress(x_task_id, 20, "Dosya yüklendi, işleme başlanıyor...")
    if RealESRGANer is None:
        return JSONResponse(status_code=500, content={"success": False, "message": "realesrgan not installed."})
    
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
            upscaler = get_upscaler()
            # Decode using raw bytes to bypass cv2 unicode limitations
            img_bytes = np.fromfile(str(src_path), np.uint8)
            img = cv2.imdecode(img_bytes, cv2.IMREAD_UNCHANGED)
            if img is None:
                raise ValueError("Image could not be read.")
            
            output, _ = upscaler.enhance(img, outscale=scale)
            
            # Encode and save via tofile to prevent Unicode save issues
            is_success, buffer = cv2.imencode(ext.lower() if ext else '.png', output)
            if is_success:
                buffer.tofile(str(out_path))
            else:
                raise ValueError("Image could not be saved.")
            
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


@app.post("/fetch-video-info")
async def fetch_video_info(req: VideoURLRequest):
    """Fetches metadata and available resolutions for the provided video URL."""
    try:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
        }

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
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Video info could not be retrieved: {str(exc)}"},
        )


@app.post("/start-download")
async def start_download(req: VideoDownloadRequest):
    """Initializes background download task and returns a tracking ID immediately."""
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

    _net = {
        "socket_timeout": 30,
        "retries": 10,
        "fragment_retries": 10,
        "retry_sleep_functions": {"http": lambda n: 2},
        "quiet": False,
        "no_warnings": False,
        "progress_hooks": [_ytdlp_progress_hook(task_id)],
    }

    # ffmpeg konumunu bildir
    if FFMPEG_DIR:
        _net["ffmpeg_location"] = FFMPEG_DIR

    if req.format_id == "mp3":
        if not FFMPEG_DIR:
            _download_tasks[task_id]["status"] = "error"
            _download_tasks[task_id]["error"] = "ffmpeg is required for MP3 conversion but not found."
            return JSONResponse(content={"success": False, "message": "ffmpeg not found, MP3 conversion cannot be performed."})
        ydl_opts = {
            **_net,
            "format": "bestaudio/best",
            "outtmpl": out_template,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }
    elif req.format_id.isdigit():
        # Belirli çözünürlük seçildi (örn. "720", "1080")
        height = req.format_id
        ydl_opts = {
            **_net,
            "format": (
                f"best[height={height}][vcodec!=none][acodec!=none]/"
                f"bestvideo[height={height}]+bestaudio/"
                f"best[height<={height}][vcodec!=none][acodec!=none]/"
                f"bestvideo[height<={height}]+bestaudio/best"
            ),
            "outtmpl": out_template,
            "merge_output_format": "mp4",
        }
    else:
        # "best" veya bilinmeyen format — en iyi kalite
        ydl_opts = {
            **_net,
            "format": "best[vcodec!=none][acodec!=none]/bestvideo+bestaudio/best",
            "outtmpl": out_template,
            "merge_output_format": "mp4",
        }

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
                task["error"] = "Downloaded file not found."
                return

            out_file = Path(files[0])
            ext = out_file.suffix.lstrip(".")
            final_filename = f"{safe_title}.{ext}"

            task["status"] = "done"
            task["progress"] = 100
            task["filename"] = final_filename
            task["filepath"] = str(out_file)

        except Exception as exc:
            task["status"] = "error"
            task["error"] = str(exc)
            # Temizlik
            cleanup_files_and_memory(*glob.glob(str(DOWNLOAD_DIR / f"{uid}.*")))

    # Background thread'de başlat — endpoint hemen döner
    asyncio.get_event_loop().run_in_executor(None, _do_download)

    return JSONResponse(content={
        "success": True,
        "task_id": task_id,
        "message": "Download started.",
    })


@app.get("/download-status/{task_id}")
async def download_status(task_id: str):
    """Polls the current download status using task ID."""
    task = _download_tasks.get(task_id)
    if not task:
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Task not found."},
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

    _download_tasks.pop(task_id, None)

    response = FileResponse(
        path=filepath,
        filename=task["filename"],
        media_type=media_type,
    )
    response.background = BackgroundTasks()
    response.background.add_task(cleanup_files_and_memory, filepath)
    return response


def _convert_image(src: str, dst: str, fmt: str) -> None:
    """Converts image formats using Pillow."""
    img = Image.open(src)

    if fmt in ("jpg", "jpeg", "bmp") and img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    if fmt == "ico":
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")
        img.thumbnail((256, 256), Image.LANCZOS)

    pillow_fmt = fmt.upper()
    if pillow_fmt == "JPG":
        pillow_fmt = "JPEG"

    img.save(dst, format=pillow_fmt)


def _convert_media(src: str, dst: str) -> None:
    """Converts video and audio media formats using ffmpeg-python."""
    (
        ffmpeg
        .input(src)
        .output(dst)
        .overwrite_output()
        .run(quiet=True)
    )


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
