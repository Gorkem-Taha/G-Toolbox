"""yt-dlp video download tasks."""

import time
from typing import Optional

from .files import cleanup_files_and_memory
from .media import FFMPEG_DIR


TEMP_MAX_AGE_HOURS = 6


def purge_finished_download_tasks(max_age_hours: int = TEMP_MAX_AGE_HOURS):
    """Forgets old video-download tasks and deletes their files."""
    cutoff = time.time() - max_age_hours * 3600
    for tid, task in list(_download_tasks.items()):
        if task.get("created", 0) < cutoff and task.get("status") != "downloading":
            _download_tasks.pop(tid, None)
            if task.get("filepath"):
                cleanup_files_and_memory(task["filepath"])


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
