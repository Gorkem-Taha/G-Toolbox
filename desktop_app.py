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


def wait_for_server(url: str, timeout: float = 10.0) -> bool:
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


def main():
    bind_host = "0.0.0.0"
    port = find_available_port(start_port=8000)
    server_url = f"http://127.0.0.1:{port}"

    print(f"[*] Starting G-Toolbox backend on port {port} (LAN & Localhost)...")
    server_thread = ServerThread(app, host=bind_host, port=port)
    server_thread.start()

    print("[*] Waiting for backend to initialize...")
    if not wait_for_server(server_url, timeout=12.0):
        print("[-] Warning: Backend initialization took longer than expected. Proceeding...")

    window_title = "G-Toolbox — All-in-One Media & AI Studio"

    print("[*] Launching Native Desktop Window...")
    window = webview.create_window(
        title=window_title,
        url=server_url,
        width=1320,
        height=880,
        min_size=(960, 640),
        text_select=True,
        zoomable=True
    )

    try:
        # Edge Chromium (WebView2) on Windows
        webview.start(gui="edgechromium", debug=False)
    finally:
        print("[*] Desktop window closed. Shutting down server...")
        server_thread.stop()


if __name__ == "__main__":
    main()
