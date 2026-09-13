"""
G-Toolbox — Desktop Native Window Launcher (PyWebView + FastAPI)
Runs the FastAPI server in a background thread and launches a native desktop application window.
"""

import os
import sys
import time
import socket
import logging
import threading
import urllib.request
from pathlib import Path

# Ensure taskbar grouping uses unique AppUserModelID on Windows (prevents python generic icon)
if sys.platform == "win32":
    try:
        import ctypes
        app_id = "gorkem.gtoolbox.studio.v4"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        pass

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

# Ensure project root is available on sys.path
if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).resolve().parent
    if hasattr(sys, "_MEIPASS"):
        sys.path.insert(0, str(sys._MEIPASS))
    sys.path.insert(0, str(APP_DIR))
else:
    APP_DIR = Path(__file__).resolve().parent
    sys.path.insert(0, str(APP_DIR))

import uvicorn
import webview
from main import app

logger = logging.getLogger("gtoolbox.desktop")


def find_available_port(start_port: int = 8000, max_attempts: int = 20) -> int:
    """Finds an available TCP port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return start_port


class ServerThread(threading.Thread):
    """Runs Uvicorn in a background daemon thread."""
    def __init__(self, app, host: str, port: int):
        super().__init__(daemon=True)
        config = uvicorn.Config(
            app=app,
            host=host,
            port=port,
            log_level="warning",
            access_log=False
        )
        self.server = uvicorn.Server(config)

    def run(self):
        self.server.run()

    def stop(self):
        self.server.should_exit = True


def wait_for_server(url: str, timeout: float = 12.0) -> bool:
    """Polls the server until it responds with HTTP 200 or timeout expires."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            req = urllib.request.Request(
                f"{url}/check-update",
                headers={"User-Agent": "GToolboxDesktop/1.0"}
            )
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.15)
    return False


def set_win32_window_icon(window_title: str, ico_path: Path):
    """Applies native G-Toolbox icon to the Win32 window and taskbar."""
    if sys.platform != "win32" or not ico_path.exists():
        return

    def _worker():
        try:
            import ctypes
            WM_SETICON = 0x0080
            ICON_SMALL = 0
            ICON_BIG = 1
            IMAGE_ICON = 1
            LR_LOADFROMFILE = 0x0010
            LR_DEFAULTSIZE = 0x0040

            h_icon = ctypes.windll.user32.LoadImageW(
                None,
                str(ico_path.resolve()),
                IMAGE_ICON,
                0, 0,
                LR_LOADFROMFILE | LR_DEFAULTSIZE
            )
            if not h_icon:
                return

            # Wait for window to be created and set icon
            for _ in range(40):
                hwnd = ctypes.windll.user32.FindWindowW(None, window_title)
                if hwnd:
                    ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, h_icon)
                    ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, h_icon)
                    break
                time.sleep(0.15)
        except Exception:
            pass

    t = threading.Thread(target=_worker, daemon=True)
    t.start()


def notify_ready():
    """Signals the splash screen launcher that the backend is ready."""
    try:
        ready_flag = APP_DIR / ".gtoolbox_ready"
        ready_flag.write_text("ready", encoding="utf-8")
    except Exception:
        pass


def cleanup_ready_flag():
    """Removes the ready flag file if it exists."""
    try:
        ready_flag = APP_DIR / ".gtoolbox_ready"
        if ready_flag.exists():
            ready_flag.unlink()
    except Exception:
        pass


def main():
    bind_host = "0.0.0.0"
    port = find_available_port(start_port=8000)
    server_url = f"http://127.0.0.1:{port}"

    cleanup_ready_flag()

    print(f"[*] Starting G-Toolbox backend on port {port} (LAN & Localhost)...")
    server_thread = ServerThread(app, host=bind_host, port=port)
    server_thread.start()

    print("[*] Waiting for backend to initialize...")
    if not wait_for_server(server_url, timeout=15.0):
        print("[-] Warning: Backend initialization took longer than expected. Proceeding...")

    window_title = "G-Toolbox — All-in-One Media & AI Studio"
    favicon_path = APP_DIR / "static" / "favicon.ico"

    # Start icon applier thread for native taskbar and titlebar icon
    set_win32_window_icon(window_title, favicon_path)

    # Signal splash launcher that window is about to open
    notify_ready()

    print("[*] Launching Native Desktop Window (Maximized / Fullscreen)...")
    window = webview.create_window(
        title=window_title,
        url=server_url,
        width=1400,
        height=900,
        min_size=(960, 640),
        maximized=True,       # Open window maximized (filling the screen)
        fullscreen=False,     # Can be toggled via UI or F11
        text_select=True,
        zoomable=True
    )

    try:
        # Edge Chromium (WebView2) on Windows, WebKitGTK on Linux
        gui_type = "edgechromium" if sys.platform == "win32" else "gtk"
        webview.start(gui=gui_type, debug=False)
    finally:
        print("[*] Desktop window closed. Shutting down server...")
        cleanup_ready_flag()
        server_thread.stop()


if __name__ == "__main__":
    main()
