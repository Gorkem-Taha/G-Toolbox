"""Update check and signed update endpoints."""

import asyncio
import shutil
import uuid

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse

from ..config import APP_VERSION, DOWNLOAD_DIR, logger
from ..files import update_progress
from ..updates import apply_latest_update, check_for_update, install_is_writable

router = APIRouter()

@router.get("/check-update")
async def check_update(request: Request):
    """Reports whether a newer release exists. Desktop health checks call this offline-safe."""
    if request.query_params.get("remote") != "1":
        return JSONResponse(content={"status": "ready", "current": APP_VERSION})
    try:
        return JSONResponse(content=await asyncio.to_thread(check_for_update))
    except Exception as e:
        return JSONResponse(status_code=502, content={"status": "error", "message": str(e)})


@router.post("/apply-update")
async def apply_update(x_task_id: str = Header(None)):
    """Downloads the latest signed release and replaces application files."""
    if not install_is_writable():
        return JSONResponse(status_code=409, content={
            "status": "error",
            "message": "This installation is read-only (e.g. AppImage). Download the new release instead.",
        })
    update_progress(x_task_id, 10, "Checking latest release...")
    work = DOWNLOAD_DIR / f"update_{uuid.uuid4().hex[:8]}"
    try:
        result = await asyncio.to_thread(
            apply_latest_update, work, lambda pct, msg: update_progress(x_task_id, pct, msg))
        update_progress(x_task_id, 100, "Update Completed!")
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Update failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": f"Update failed: {str(e)}"})
    finally:
        shutil.rmtree(work, ignore_errors=True)
