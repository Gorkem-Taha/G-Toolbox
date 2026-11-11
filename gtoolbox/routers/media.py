"""Media converter, metadata, GIF/WebP, subtitles, audio effects and denoise endpoints."""

import asyncio
import os
import re
import subprocess
import uuid
from pathlib import Path
from typing import Optional

from PIL import ExifTags, Image
from fastapi import APIRouter, BackgroundTasks, File, Form, Header, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from ..config import AUDIO_EXTENSIONS, DOWNLOAD_DIR, IMAGE_EXTENSIONS, MIME_MAP, UPLOAD_DIR, VIDEO_EXTENSIONS, logger
from ..files import _safe_filename, cleanup_files_and_memory, save_upload, update_progress
from ..media import MEDIA_JOB_TIMEOUT, _convert_image, _convert_media, _guess_media_type, _normalize_target_format, atempo_chain, ffmpeg_error, ffmpeg_exe, probe_sample_rate, speed_pitch_filter, strip_image_metadata

router = APIRouter()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Uploads a file to the temporary storage directory."""
    try:
        safe_name = _safe_filename(file.filename)
        dest = UPLOAD_DIR / safe_name
        await save_upload(file, dest)

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


@router.post("/convert")
async def convert_file(
    file: UploadFile = File(...),
    target_format: str = Form(...),
    background_tasks: BackgroundTasks = None,
    x_task_id: str = Header(None)
):
    """Handles standard media file conversions."""
    update_progress(x_task_id, 20, "File uploaded, initializing conversion...")
    target_format = _normalize_target_format(target_format)
    if target_format is None:
        return JSONResponse(status_code=400, content={"success": False, "message": "Unsupported target format."})
    uid = uuid.uuid4().hex[:8]
    safe_name = _safe_filename(file.filename)

    # Gelen dosyayı geçici olarak uploads/ klasörüne kaydet
    src_path = UPLOAD_DIR / f"{uid}_{safe_name}"
    await save_upload(file, src_path)

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
            await asyncio.to_thread(_convert_image, str(src_path), str(out_path), target_format)
        else:
            await asyncio.to_thread(_convert_media, str(src_path), str(out_path))

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


@router.post("/convert-universal")
async def convert_universal(
    file: UploadFile = File(...),
    target_format: str = Form(...),
    background_tasks: BackgroundTasks = None,
    x_task_id: str = Header(None)
):
    """Handles universal format conversions across image, audio, and video types."""
    update_progress(x_task_id, 20, "File uploaded, initializing conversion...")
    target_format = _normalize_target_format(target_format)
    if target_format is None:
        return JSONResponse(status_code=400, content={"success": False, "message": "Unsupported target format."})
    uid = uuid.uuid4().hex[:8]
    safe_name = _safe_filename(file.filename)

    stem = Path(safe_name).stem
    out_name = f"{stem}_{uid}.{target_format}"
    out_path = DOWNLOAD_DIR / out_name

    src_path = UPLOAD_DIR / f"uni_{uid}_{safe_name}"
    await save_upload(file, src_path)

    ext = Path(safe_name).suffix.lower().lstrip(".")

    images = {"png", "jpg", "jpeg", "webp", "bmp", "gif", "tiff", "ico"}
    videos_audios = {"mp4", "avi", "mkv", "mov", "webm", "flv", "wmv", "mp3", "wav", "ogg", "flac", "aac", "m4a", "wma"}

    try:
        update_progress(x_task_id, 50, "Model is executing. This may take a while depending on file size...")
        if ext in images and target_format in images:
            await asyncio.to_thread(_convert_image, str(src_path), str(out_path), target_format)
            
        elif ext in videos_audios and target_format in videos_audios:
            await asyncio.to_thread(_convert_media, str(src_path), str(out_path))

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


# ── EXIF & Metadata Inspector / Stripper ──────────────────────────
@router.post("/view-metadata")
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


@router.post("/strip-metadata")
async def strip_metadata(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Completely strips EXIF, GPS, camera model, and private metadata from an image."""
    safe_name = _safe_filename(file.filename)
    dest_path = DOWNLOAD_DIR / f"clean_{uuid.uuid4().hex}_{safe_name}"
    try:
        fmt = await asyncio.to_thread(strip_image_metadata, file.file, dest_path)
        background_tasks.add_task(cleanup_files_and_memory, dest_path)
        return FileResponse(
            dest_path,
            media_type=Image.MIME.get(fmt, "application/octet-stream"),
            filename=f"clean_{safe_name}"
        )
    except Exception as e:
        cleanup_files_and_memory(dest_path)
        return JSONResponse(status_code=500, content={"status": "error", "message": f"Strip failed: {str(e)}"})


# ── Video to GIF / WebP Animation ────────────────────────────────
@router.post("/video-to-anim")
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
    # Validate user parameters before they reach the ffmpeg command line.
    start_time = str(start_time).strip()
    if not re.fullmatch(r"(\d{1,2}:){0,2}\d{1,5}(\.\d{1,3})?", start_time):
        return JSONResponse(status_code=400, content={"status": "error",
                            "message": "Start time must look like HH:MM:SS, MM:SS or seconds."})
    duration = max(0.1, min(60.0, float(duration)))
    fps = max(1, min(60, int(fps)))
    width = max(64, min(1920, int(width)))
    quality = max(1, min(100, int(quality)))
    update_progress(x_task_id, 10, "Uploading video for animation render...")
    safe_name = _safe_filename(file.filename)
    input_path = UPLOAD_DIR / f"{uuid.uuid4().hex}_{safe_name}"
    
    await save_upload(file, input_path)

    out_ext = "webp" if anim_format.lower() == "webp" else "gif"
    out_path = DOWNLOAD_DIR / f"{Path(safe_name).stem}_anim_{uuid.uuid4().hex[:6]}.{out_ext}"

    def _render():
        try:
            update_progress(x_task_id, 40, f"Rendering high-quality animated {out_ext.upper()} via FFmpeg...")
            ffmpeg_bin = ffmpeg_exe()

            if out_ext == "gif":
                vf = f"fps={fps},scale={width}:-2:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"
                cmd = [
                    ffmpeg_bin, "-y",
                    "-ss", str(start_time),
                    "-t", str(duration),
                    "-i", str(input_path),
                    "-vf", vf,
                    str(out_path)
                ]
            else:
                vf = f"fps={fps},scale={width}:-2:flags=lanczos"
                cmd = [
                    ffmpeg_bin, "-y",
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

            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=MEDIA_JOB_TIMEOUT)
            if proc.returncode != 0:
                raise ffmpeg_error(proc, "FFmpeg error")

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


# ── Video Hardsub Burner ──────────────────────────────────────────
@router.post("/burn-subtitles")
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

    sub_ext = Path(safe_sub).suffix.lower().lstrip(".")
    if sub_ext not in ("srt", "vtt", "ass", "ssa"):
        return JSONResponse(status_code=400, content={"status": "error",
                            "message": "Subtitle must be .srt, .vtt, .ass or .ssa"})

    video_path = UPLOAD_DIR / f"v_{uid}_{safe_video}"
    # Fixed, filter-safe name: the subtitles= filter option is parsed by ffmpeg's
    # filtergraph syntax, where quotes, colons and backslashes are special.
    sub_name = f"sub_{uid}.{sub_ext}"
    sub_path = UPLOAD_DIR / sub_name
    out_name = f"{Path(safe_video).stem}_subbed_{uid}.mp4"
    out_path = DOWNLOAD_DIR / out_name

    await save_upload(video, video_path)
    await save_upload(subtitle, sub_path)

    color_map = {
        "white": "&H00FFFFFF",
        "yellow": "&H0000FFFF",
        "cyan": "&H00FFFF00",
        "green": "&H0000FF00",
    }
    color_code = color_map.get(font_color.lower(), "&H00FFFFFF")
    font_size = max(8, min(120, int(font_size)))

    def _burn():
        try:
            update_progress(x_task_id, 40, "Burning subtitles into video stream...")
            style = f"FontSize={font_size},PrimaryColour={color_code},OutlineColour=&H00000000,BorderStyle=3,Outline=2"
            vf = f"subtitles={sub_name}:force_style='{style}'"

            def run(audio_args):
                cmd = [
                    ffmpeg_exe(), "-hide_banner", "-y",
                    "-i", str(video_path.resolve()),
                    "-vf", vf,
                    "-c:v", "libx264", "-preset", "fast", "-crf", "22",
                    *audio_args,
                    "-movflags", "+faststart",
                    str(out_path.resolve()),
                ]
                # cwd = upload dir so the filter only sees the safe relative name
                return subprocess.run(cmd, capture_output=True, text=True,
                                      timeout=MEDIA_JOB_TIMEOUT, cwd=str(UPLOAD_DIR))

            proc = run(["-c:a", "copy"])
            if proc.returncode != 0:
                # Source audio codec may not fit in MP4 (e.g. Vorbis): re-encode it.
                proc = run(["-c:a", "aac", "-b:a", "192k"])
            if proc.returncode != 0:
                raise ffmpeg_error(proc, "Subtitle burn error")

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


# ── Audio Speed, Pitch & Effects Engine (Slowed+Reverb / Nightcore) ─
@router.post("/audio-effects")
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

    await save_upload(file, input_path)

    enable_reverb = add_reverb or (str(reverb).lower() in ("true", "1", "yes"))

    def _apply_fx():
        try:
            update_progress(x_task_id, 40, "Applying audio effects filter chain...")
            ffmpeg_bin = ffmpeg_exe()

            # Use the real input sample rate (48 kHz is common) instead of assuming 44.1 kHz.
            sr = probe_sample_rate(input_path)
            reverb = "aecho=0.8:0.88:60:0.4"
            filters = []
            if preset == "slowed_reverb":
                filters += [atempo_chain(0.85), reverb]
            elif preset == "nightcore":
                filters.append(speed_pitch_filter(sr, 1.25, 1.25))
            elif preset == "speed_1_5x":
                filters.append(atempo_chain(1.5))
            elif preset == "slow_0_75x":
                filters.append(atempo_chain(0.75))
            else:
                clamped_tempo = max(0.5, min(2.0, tempo))
                clamped_pitch = max(0.5, min(2.0, pitch))
                filters.append(speed_pitch_filter(sr, clamped_tempo, clamped_pitch))
                if enable_reverb:
                    filters.append(reverb)

            af = ",".join(filters) if filters else "atempo=1.0"

            cmd = [
                ffmpeg_bin, "-y",
                "-i", str(input_path),
                "-vn",
                "-af", af,
                "-q:a", "2",
                str(out_path)
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=MEDIA_JOB_TIMEOUT)
            if proc.returncode != 0:
                raise ffmpeg_error(proc, "Audio effect error")

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
@router.post("/clean-audio-noise")
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

    await save_upload(file, input_path)

    # Calculate filter string
    is_voice_focus = str(voice_focus).lower() in ("true", "1", "yes")
    if noise_reduction_db is not None:
        # afftdn accepts a noise floor between -80 and -20 dB
        nr_val = max(-80.0, min(-20.0, -abs(float(noise_reduction_db))))
        denoise_filter = f"afftdn=nf={nr_val:g}:tn=1"
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
            update_progress(x_task_id, 40, "Processing audio with FFT noise suppressor...")
            ffmpeg_bin = ffmpeg_exe()

            if is_video:
                # Pick an audio codec the output container can hold (WebM: Opus only).
                audio_codec = {"webm": ["libopus", "-b:a", "160k"],
                               "wmv": ["wmav2", "-b:a", "192k"]}.get(out_ext, ["aac", "-b:a", "192k"])
                cmd = [
                    ffmpeg_bin, "-y",
                    "-i", str(input_path),
                    "-map", "0:v?", "-map", "0:a?",
                    "-c:v", "copy",
                    "-af", af,
                    "-c:a", *audio_codec,
                    str(out_path)
                ]
            else:
                cmd = [
                    ffmpeg_bin, "-y",
                    "-i", str(input_path),
                    "-vn",
                    "-af", af,
                    "-q:a", "2",
                    str(out_path)
                ]

            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=MEDIA_JOB_TIMEOUT)
            if proc.returncode != 0:
                raise ffmpeg_error(proc, "Denoise error")

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
