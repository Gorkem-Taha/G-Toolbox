"""FastAPI application factory: middleware, error handling, static files, routers."""

import asyncio
import html
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import security
from .config import APP_VERSION, STATIC_DIR, lan_access_enabled, logger
from .downloads import TEMP_MAX_AGE_HOURS, purge_finished_download_tasks
from .files import purge_stale_files
from .security import access_guard, get_lan_ip

from .routers import ai as ai_routes, documents as document_routes, media as media_routes, system as system_routes, updates as update_routes, video as video_routes

@asynccontextmanager
async def lifespan(_app):
    task = asyncio.create_task(_maintenance_loop())
    try:
        yield
    finally:
        task.cancel()


async def global_exception_handler(request: Request, exc: Exception):
    err_tb = traceback.format_exc()
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}\n{err_tb}")
    if request.url.path == "/" or "text/html" in request.headers.get("accept", ""):
        return HTMLResponse(
            status_code=500,
            content="<!DOCTYPE html><html><head><meta charset='utf-8'><title>G-Toolbox Hata</title></head><body style='font-family:sans-serif;background:#0d1117;color:#c9d1d9;padding:30px;'>"
                    "<h2 style='color:#f85149;'>⚠️ G-Toolbox — Sunucu Hatası (500)</h2>"
                    f"<p>İstek: <code>{html.escape(request.method)} {html.escape(request.url.path)}</code></p>"
                    f"<p>Hata: <b>{html.escape(str(exc))}</b></p>"
                    "<p>Ayrıntılar sunucu günlüğüne yazıldı.</p>"
                    "</body></html>"
        )
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": str(exc), "path": request.url.path}
    )


async def _maintenance_loop():
    """Disk hygiene at startup and then every hour (not only on startup)."""
    while True:
        try:
            await asyncio.to_thread(purge_stale_files, TEMP_MAX_AGE_HOURS)
            purge_finished_download_tasks()
        except Exception as e:
            logger.warning(f"Maintenance purge warning: {e}")
        await asyncio.sleep(3600)


def run_server(port: int = 8000, open_browser: bool = True) -> None:
    """Runs the API in browser mode: `python main.py [--lan] [--port N] [--no-browser]`."""
    import uvicorn
    host = "0.0.0.0" if lan_access_enabled() else "127.0.0.1"
    if open_browser:
        import threading
        import webbrowser
        threading.Timer(1.5, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()
    if host != "127.0.0.1":
        logger.warning(f"LAN access enabled. Pairing link: http://{get_lan_ip()}:{port}/?token={security.ACCESS_TOKEN}")
    uvicorn.run(app, host=host, port=port, log_level="info")


app = FastAPI(title="G-Toolbox", version=APP_VERSION, lifespan=lifespan)
app.middleware("http")(access_guard)
app.add_exception_handler(Exception, global_exception_handler)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
for _routes in (system_routes, media_routes, ai_routes, video_routes, document_routes, update_routes):
    app.include_router(_routes.router)
