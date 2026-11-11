"""PDF toolkit and AES vault endpoints."""

import asyncio
import shutil
import uuid
import zipfile
from pathlib import Path
from typing import List, Optional

import pyAesCrypt
from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, Header, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from ..config import DOWNLOAD_DIR, UPLOAD_DIR
from ..files import _safe_arcname, _safe_filename, cleanup_files_and_memory, save_upload, update_progress
from ..media import _guess_media_type, parse_page_ranges

router = APIRouter()

@router.post("/encrypt-file")
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
        await save_upload(file, src_path)
        out_name = f"{safe_name}.enc"
    else:
        safe_name = "vault_archive.zip"
        src_path = UPLOAD_DIR / f"enc_{uid}_{safe_name}"
        update_progress(x_task_id, 30, "Converting folder/multi-files to zip...")

        def _build_zip():
            with zipfile.ZipFile(src_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for f in files:
                    f.file.seek(0)
                    with zf.open(_safe_arcname(f.filename), "w") as dst:
                        shutil.copyfileobj(f.file, dst, 1024 * 1024)

        await asyncio.to_thread(_build_zip)
        out_name = f"{safe_name}.enc"

    # Unique on disk; the user still downloads `out_name`.
    out_path = DOWNLOAD_DIR / f"{uid}_{out_name}"
    
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


@router.post("/decrypt-file")
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
    await save_upload(file, src_path)
        
    if safe_name.endswith(".enc"):
        out_name = safe_name[:-4]
    else:
        out_name = f"decrypted_{safe_name}"

    out_path = DOWNLOAD_DIR / f"{uid}_{out_name}"
    
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


# ── PDF Swiss Army Toolkit ─────────────────────────────────────────
@router.post("/pdf-merge")
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
        await save_upload(f, p)
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


@router.post("/pdf-split")
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

    await save_upload(file, src_path)

    def _do_split():
        try:
            update_progress(x_task_id, 50, f"Extracting pages ({target_range})...")
            reader = pypdf.PdfReader(str(src_path))
            writer = pypdf.PdfWriter()
            total_pages = len(reader.pages)

            for page_idx in parse_page_ranges(target_range, total_pages):
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
    except ValueError as e:
        return JSONResponse(status_code=400, content={"status": "error", "message": str(e)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": f"Split failed: {str(e)}"})


@router.post("/pdf-extract-text")
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

    await save_upload(file, src_path)

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
