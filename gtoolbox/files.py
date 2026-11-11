"""Upload storage, temp-file cleanup and task progress tracking."""

import asyncio
import os
import re
import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile

from .config import DOWNLOAD_DIR, UPLOAD_DIR, logger


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


def _path_inside(path: Path, base: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def _copy_upload(upload: UploadFile, dest) -> None:
    upload.file.seek(0)
    with open(dest, "wb") as out:
        shutil.copyfileobj(upload.file, out, 1024 * 1024)


async def save_upload(upload: UploadFile, dest) -> None:
    """Writes an uploaded file to disk without blocking the event loop."""
    await asyncio.to_thread(_copy_upload, upload, dest)


def _safe_arcname(raw: str) -> str:
    """Relative folder path from the browser, without '..', drive letters or leading slashes,
    so the vault can never extract outside its folder later (zip-slip)."""
    parts = [p for p in re.split(r"[\\/]+", str(raw or "")) if p not in ("", ".", "..")]
    parts = [re.sub(r"^[A-Za-z]:", "", p) or "_" for p in parts]
    return "/".join(parts) or uuid.uuid4().hex
