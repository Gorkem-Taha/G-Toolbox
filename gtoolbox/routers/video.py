"""Video downloader endpoints."""

import asyncio
import glob
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Optional

import yt_dlp
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from ..config import DOWNLOAD_DIR, PIP_TARGET, logger
from ..dialogs import _open_native_save_dialog
from ..downloads import _build_ytdlp_opts, _download_tasks
from ..files import cleanup_files_and_memory
from ..media import FFMPEG_DIR, _guess_media_type

router = APIRouter()

class VideoURLRequest(BaseModel):
    url: str


class VideoDownloadRequest(BaseModel):
    url: str
    format_id: str
    title: str = "video"


@router.post("/fetch-video-info")
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


@router.post("/start-download")
async def start_download(req: VideoDownloadRequest):
    """Initializes background download task with 403 protection and returns a tracking ID immediately."""
    task_id = uuid.uuid4().hex[:12]
    uid = task_id[:8]
    out_template = str(DOWNLOAD_DIR / f"{uid}.%(ext)s")

    _download_tasks[task_id] = {
        "created": time.time(),
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


@router.get("/download-status/{task_id}")
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


@router.post("/api/save-task-file")
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


@router.get("/download-file/{task_id}")
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


@router.post("/update-ytdlp")
async def update_ytdlp():
    """Updates yt-dlp to the latest version to prevent YouTube streaming download breakages."""
    def _run_update():
        try:
            cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"]
            if PIP_TARGET:
                cmd += ["--target", PIP_TARGET]
            subprocess.run(cmd, capture_output=True, text=True, timeout=90)
            v_proc = subprocess.run([sys.executable, "-m", "yt_dlp", "--version"], capture_output=True, text=True, timeout=10)
            ver = v_proc.stdout.strip() if v_proc.returncode == 0 else "Latest"
            return {"success": True, "version": ver, "message": f"yt-dlp engine successfully updated to {ver}."}
        except Exception as e:
            return {"success": False, "message": f"Update failed: {str(e)}"}

    res = await asyncio.to_thread(_run_update)
    code = 200 if res.get("success") else 500
    return JSONResponse(status_code=code, content=res)
