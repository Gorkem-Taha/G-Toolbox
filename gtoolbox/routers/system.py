"""Page, service worker, pairing, progress, hardware status and host-only actions."""

import asyncio
import os
import sys
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from .. import ai, security
from ..ai import purge_vram_and_models
from ..config import BASE_DIR, RESOURCE_DIR, STATIC_DIR, TEMPLATES_DIR, lan_access_enabled, load_settings, logger, save_settings, templates
from ..dialogs import _open_native_save_dialog
from ..files import progress_store, save_upload
from ..security import _is_loopback, get_lan_ip, rotate_access_token

router = APIRouter()

@router.get("/api/network-info")
async def get_network_info(request: Request):
    """Returns host LAN network details for easy mobile pairing."""
    host_ip = get_lan_ip()
    port = request.url.port or 8000
    lan_enabled = lan_access_enabled()
    client_host = request.client.host if request.client else ""
    payload = {
        "lan_ip": host_ip,
        "port": port,
        "lan_enabled": lan_enabled,
        "mobile_url": f"http://{host_ip}:{port}" if lan_enabled else "",
    }
    # Only the host computer gets the pairing link (it contains the secret token).
    if lan_enabled and _is_loopback(client_host):
        payload["pairing_url"] = f"http://{host_ip}:{port}/?token={security.ACCESS_TOKEN}"
    return JSONResponse(payload)


class LanAccessRequest(BaseModel):
    enabled: bool
    rotate_token: bool = False


@router.post("/api/lan-access")
async def set_lan_access(req: LanAccessRequest):
    """Enables/disables LAN (phone) access. Takes effect after restart. Host-only."""
    settings = load_settings()
    settings["lan_access"] = bool(req.enabled)
    save_settings(settings)
    if req.rotate_token:
        rotate_access_token()
    return JSONResponse({
        "success": True,
        "lan_enabled": settings["lan_access"],
        "restart_required": True,
    })


@router.get("/progress/{task_id}")
async def get_progress(task_id: str):
    """Returns the current progress status for a given task ID."""
    info = progress_store.get(task_id, {"progress": 0, "message": ""})
    return JSONResponse(content={"progress": info.get("progress", 0), "message": info.get("message", "")})


@router.get("/")
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


@router.get("/sw.js")
async def service_worker():
    """Serves the service worker from the site root so its scope is "/"."""
    return FileResponse(
        str(STATIC_DIR / "sw.js"),
        media_type="application/javascript",
        headers={"Cache-Control": "no-cache"},
    )


@router.post("/api/save-blob-file")
async def save_blob_file(
    file: UploadFile = File(...),
    suggested_filename: str = Form("dosya")
):
    """Saves uploaded blob directly to user-chosen destination via native Windows Save As dialog."""
    suggested_filename = Path(suggested_filename or "").name or "dosya"
    ext = Path(suggested_filename).suffix or Path(file.filename or "").suffix
    chosen = await asyncio.to_thread(_open_native_save_dialog, suggested_filename, ext)
    if chosen == "CANCELED":
        return JSONResponse(content={"success": False, "canceled": True, "message": "Kaydetme iptal edildi."})
    if not chosen:
        return JSONResponse(content={"success": False, "canceled": False, "native_unsupported": True})

    try:
        await save_upload(file, chosen)
        return JSONResponse(content={
            "success": True,
            "canceled": False,
            "saved_path": str(chosen),
            "filename": Path(chosen).name
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dosya yazılamadı: {str(e)}")


@router.post("/api/restart-as-admin")
async def restart_as_admin():
    """Relaunches G-Toolbox as Administrator with UAC confirmation and closes the current instance."""
    if sys.platform != "win32":
        return JSONResponse(content={"success": False, "message": "Only supported on Windows."})
    try:
        import ctypes
        base_exe = BASE_DIR / "G-Toolbox.exe"
        target = str(base_exe) if base_exe.exists() else sys.executable
        args = "" if base_exe.exists() else f'"{BASE_DIR / "desktop_app.py"}"'
        ctypes.windll.shell32.ShellExecuteW(None, "runas", target, args, str(BASE_DIR), 1)

        asyncio.get_event_loop().call_later(1.0, lambda: os._exit(0))
        return JSONResponse(content={"success": True, "message": "Restarting as Administrator..."})
    except Exception as e:
        logger.error(f"Restart as admin failed: {e}")
        return JSONResponse(status_code=500, content={"success": False, "message": str(e)})


@router.post("/api/open-security-settings")
async def open_security_settings():
    """Opens Windows Security App & browser control settings."""
    if sys.platform == "win32":
        try:
            os.system("start windowsdefender://appbrowser")
            return JSONResponse(content={"success": True})
        except Exception as e:
            return JSONResponse(status_code=500, content={"success": False, "message": str(e)})
    return JSONResponse(content={"success": False, "message": "Only supported on Windows."})


@router.get("/api/system-status")
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
            "upscalers": len(ai._UPSCALER_INSTANCES),
            "lama": ai._LAMA_INSTANCE is not None,
            "rembg": ai._REMBG_SESSION is not None,
            "whisper": len(ai._WHISPER_MODELS)
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


@router.post("/api/purge-vram")
async def api_purge_vram():
    """Manually purges VRAM and unloads models."""
    purge_vram_and_models()
    status_response = await get_system_status()
    import json
    status_dict = json.loads(status_response.body.decode("utf-8"))
    return JSONResponse({"success": True, "message": "VRAM and AI models successfully unloaded.", "status": status_dict})
