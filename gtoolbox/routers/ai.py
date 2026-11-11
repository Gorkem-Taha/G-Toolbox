"""AI tool endpoints (background removal, inpainting, upscaling, stems, transcription) and AI setup."""

import asyncio
import shutil
import subprocess
import sys
import uuid
import zipfile
from pathlib import Path

from PIL import Image
from fastapi import APIRouter, BackgroundTasks, File, Form, Header, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from .. import ai
from ..ai import check_ai_models_status, delete_ai_model_files, ensure_ai_runtime, get_lama_model, get_rembg_session, get_upscaler, get_whisper_model, purge_vram_and_models, start_ai_install
from ..config import DOWNLOAD_DIR, IMAGE_EXTENSIONS, UPLOAD_DIR, logger
from ..files import _safe_filename, cleanup_files_and_memory, save_upload, update_progress
from ..media import MEDIA_JOB_TIMEOUT, _guess_media_type, ffmpeg_error, format_timestamp

router = APIRouter()

@router.post("/remove-background")
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
    await save_upload(file, src_path)

    stem = Path(safe_name).stem
    out_name = f"{stem}_nobg_{uid}.png"
    out_path = DOWNLOAD_DIR / out_name

    if not ai.REMBG_AVAILABLE or ai.rembg_remove is None:
        cleanup_files_and_memory(src_path)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Arka plan silme AI motoru (rembg) yüklü değil. Lütfen Ayarlar > AI Kurulumu yapın.",
                "detail": "rembg library is not installed yet. Please complete AI setup."
            }
        )

    try:
        update_progress(x_task_id, 50, "AI model is executing. This process relies on CPU and GPU overhead...")

        def process_rembg():
            session = get_rembg_session()
            img = Image.open(src_path)
            try:
                from PIL import ImageOps
                img = ImageOps.exif_transpose(img)
            except Exception:
                pass

            # Convert non-RGB/RGBA modes (CMYK, P, L, 1, etc.) cleanly
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGBA" if "A" in img.mode or "transparency" in img.info else "RGB")

            result = ai.rembg_remove(img, session=session)
            if isinstance(result, Image.Image):
                if result.mode != "RGBA":
                    result = result.convert("RGBA")
                result.save(str(out_path), format="PNG")
            elif isinstance(result, (bytes, bytearray)):
                with open(out_path, "wb") as f:
                    f.write(result)
            elif isinstance(result, ai.np.ndarray):
                res_img = Image.fromarray(result)
                if res_img.mode != "RGBA":
                    res_img = res_img.convert("RGBA")
                res_img.save(str(out_path), format="PNG")
            else:
                raise ValueError(f"Unexpected rembg output format: {type(result)}")

        await asyncio.to_thread(process_rembg)

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
        logger.error(f"Remove background error: {exc}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Background removal error: {str(exc)}", "detail": str(exc)},
        )


@router.post("/magic-erase")
async def magic_erase(
    image: UploadFile = File(...),
    mask: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    x_task_id: str = Header(None)
):
    """Erases specified masked regions from an image using the LaMa inpainting model."""
    ensure_ai_runtime()
    update_progress(x_task_id, 20, "File uploaded, initializing process...")
    if not ai.LAMA_AVAILABLE:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": "simple-lama-inpainting library is not installed yet. Please complete AI setup."}
        )

    uid = uuid.uuid4().hex[:8]
    safe_name = _safe_filename(image.filename)
    
    img_path = UPLOAD_DIR / f"magic_{uid}_{safe_name}"
    mask_path = UPLOAD_DIR / f"mask_{uid}_{safe_name}"
    
    stem = Path(safe_name).stem
    out_name = f"{stem}_erased_{uid}.png"
    out_path = DOWNLOAD_DIR / out_name

    await save_upload(image, img_path)
        
    await save_upload(mask, mask_path)

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
@router.post("/upscale-image")
async def upscale_image(
    file: UploadFile = File(...),
    scale: int = Form(4),
    model_type: str = Form("general"),
    background_tasks: BackgroundTasks = None,
    x_task_id: str = Header(None)
):
    ensure_ai_runtime()
    update_progress(x_task_id, 20, "File uploaded, starting upscale process...")
    if ai.RealESRGANer is None:
        return JSONResponse(status_code=500, content={"success": False, "message": "realesrgan or PyTorch is not installed yet. Please complete AI setup."})
    
    if scale not in [2, 4]:
        scale = 4
        
    uid = uuid.uuid4().hex[:8]
    safe_name = _safe_filename(file.filename)
    stem = Path(safe_name).stem
    ext = Path(safe_name).suffix or ".png"
    
    src_path = UPLOAD_DIR / f"upscale_{uid}{ext}"
    out_name = f"{stem}_upscaled_{scale}x_{uid}{ext}"
    out_path = DOWNLOAD_DIR / out_name
    
    await save_upload(file, src_path)
        
    try:
        update_progress(x_task_id, 50, "Model çalışıyor (Bu işlem biraz sürebilir)...")
        def process_upscale():
            upscaler = get_upscaler(model_type=model_type)
            # Decode using raw bytes to bypass cv2 unicode limitations
            img_bytes = ai.np.fromfile(str(src_path), ai.np.uint8)
            img = ai.cv2.imdecode(img_bytes, ai.cv2.IMREAD_UNCHANGED)
            if img is None:
                raise ValueError("Image could not be read or is corrupted.")
            
            # Dimension safety guard: avoid extreme resolutions causing system freeze / OOM
            h, w = img.shape[:2]
            max_dim = 3840
            if max(h, w) > max_dim:
                factor = max_dim / max(h, w)
                new_w, new_h = int(w * factor), int(h * factor)
                img = ai.cv2.resize(img, (new_w, new_h), interpolation=ai.cv2.INTER_AREA)

            # Handle transparency (RGBA) and grayscale channels safely
            has_alpha = False
            alpha_channel = None

            if len(img.shape) == 2:
                # 1-channel Grayscale -> convert to 3-channel BGR
                img = ai.cv2.cvtColor(img, ai.cv2.COLOR_GRAY2BGR)
            elif len(img.shape) == 3:
                if img.shape[2] == 4:
                    # 4-channel RGBA: extract alpha, enhance BGR, resize alpha with Lanczos
                    has_alpha = True
                    alpha_channel = img[:, :, 3]
                    img = img[:, :, :3]
                elif img.shape[2] == 1:
                    img = ai.cv2.cvtColor(img, ai.cv2.COLOR_GRAY2BGR)
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
                alpha_resized = ai.cv2.resize(alpha_channel, (out_w, out_h), interpolation=ai.cv2.INTER_LANCZOS4)
                if len(output.shape) == 3 and output.shape[2] == 3:
                    output = ai.np.dstack([output, alpha_resized])

            # Choose safe output extension (RGBA requires PNG format)
            # Keep the input format when OpenCV can write it; PNG otherwise
            # (GIF/ICO input, or transparency that JPEG/BMP cannot hold).
            out_ext = ext.lower() if ext.lower() in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff") else ".png"
            if has_alpha and out_ext in (".jpg", ".jpeg", ".bmp"):
                out_ext = ".png"
            final_path = out_path.with_suffix(out_ext)

            # Encode and save via tofile to prevent Unicode save issues
            is_success, buffer = ai.cv2.imencode(out_ext, output)
            if not is_success:
                raise ValueError("Upscaled image could not be encoded.")
            buffer.tofile(str(final_path))
            return final_path

        out_path = await asyncio.to_thread(process_upscale)
        
        update_progress(x_task_id, 90, "Packaging results...")
        if background_tasks:
            background_tasks.add_task(cleanup_files_and_memory, src_path, out_path)
        else:
            cleanup_files_and_memory(src_path)
            
        update_progress(x_task_id, 100, "Completed!")
        return FileResponse(
            path=str(out_path),
            filename=out_path.name,
            media_type=_guess_media_type(out_path.suffix.lstrip(".").lower())
        )
    except Exception as exc:
        cleanup_files_and_memory(src_path, out_path)
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Upscale error: {str(exc)}"}
        )


@router.get("/api/ai-status")
async def get_ai_status():
    """Returns local AI model presence and installation status."""
    st = await asyncio.to_thread(check_ai_models_status)
    for m in st.get("models", {}).values():
        m.pop("path", None)  # do not expose local file system layout
    st["install_progress"] = ai._AI_INSTALL_PROGRESS
    return JSONResponse(content=st)


@router.post("/api/install-ai-models")
async def start_install_ai_models():
    """Starts background download of all required AI models."""
    if not start_ai_install():
        return JSONResponse(content={"success": True, "message": "Already downloading."})
    return JSONResponse(content={"success": True, "message": "Model download started."})


@router.post("/api/delete-ai-models")
async def delete_ai_models():
    """Deletes all local AI model weights from disk to free up disk space and flushes RAM/VRAM."""
    purge_vram_and_models()
    freed_mb, deleted_files = delete_ai_model_files()

    return JSONResponse(content={
        "success": True,
        "freed_mb": freed_mb,
        "deleted_files": deleted_files,
        "message": f"AI models deleted. {freed_mb} MB disk space freed."
    })


# ── Demucs Audio Stem Separation ──────────────────────────────────
@router.post("/separate-audio")
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
    
    await save_upload(file, input_path)

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
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=MEDIA_JOB_TIMEOUT)
                if proc.returncode != 0:
                    raise ffmpeg_error(proc, "Demucs processing error")

            update_progress(x_task_id, 80, "Compressing separated audio stems into ZIP...")
            track_dirs = list((out_folder / "htdemucs").glob("*"))
            if not track_dirs:
                raise RuntimeError("No output stems produced by Demucs.")
            
            target_track_dir = track_dirs[0]
            zip_filename = f"{Path(safe_name).stem}_separated_stems.zip"
            zip_path = DOWNLOAD_DIR / f"{uuid.uuid4().hex[:8]}_{zip_filename}"
            
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
            filename=zip_path.name.split("_", 1)[1]
        )
    except Exception as e:
        logger.error(f"Demucs separation failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


@router.post("/transcribe-media")
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

    await save_upload(file, input_path)

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
            tag = uuid.uuid4().hex[:8]
            if output_format == "srt":
                out_path = DOWNLOAD_DIR / f"{tag}_{base_stem}_subtitles.srt"
                out_path.write_text("\n".join(srt_entries), encoding="utf-8")
                media_type = "text/plain"
            elif output_format == "vtt":
                out_path = DOWNLOAD_DIR / f"{tag}_{base_stem}_subtitles.vtt"
                cues = [
                    f"{format_timestamp(seg['start']).replace(',', '.')} --> "
                    f"{format_timestamp(seg['end']).replace(',', '.')}\n{seg['text']}\n"
                    for seg in raw_segments
                ]
                out_path.write_text("WEBVTT\n\n" + "\n".join(cues), encoding="utf-8")
                media_type = "text/vtt"
            elif output_format == "json":
                return {
                    "language": info.language,
                    "duration": info.duration,
                    "full_text": "\n".join(text_lines),
                    "segments": raw_segments
                }
            else:
                out_path = DOWNLOAD_DIR / f"{tag}_{base_stem}_transcript.txt"
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
        return FileResponse(out_path, media_type=media_type, filename=out_path.name.split("_", 1)[1])
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
