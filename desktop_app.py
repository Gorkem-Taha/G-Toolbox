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

# Ensure project root is available on sys.path
if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).resolve().parent
    if hasattr(sys, "_MEIPASS"):
        sys.path.insert(0, str(sys._MEIPASS))
    sys.path.insert(0, str(APP_DIR))
else:
    APP_DIR = Path(__file__).resolve().parent
    sys.path.insert(0, str(APP_DIR))

# Setup file logger so exceptions and diagnostics are recorded
LOG_DIR = Path(os.environ["GTOOLBOX_DATA_DIR"]).expanduser() if os.environ.get("GTOOLBOX_DATA_DIR") else APP_DIR
LOG_DIR.mkdir(parents=True, exist_ok=True)
log_path = LOG_DIR / "desktop.log"
try:
    log_fp = open(log_path, "a", encoding="utf-8", buffering=1)
    if sys.stdout is None:
        sys.stdout = log_fp
    if sys.stderr is None:
        sys.stderr = log_fp
except Exception:
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")

import uvicorn
from gtoolbox import dialogs
from gtoolbox.app import app
from gtoolbox.config import lan_access_enabled

# pywebview needs a GUI toolkit binding (WebView2 on Windows, GTK/Qt on Linux).
# Without one (e.g. the AppImage's bundled Python) fall back to the browser.
try:
    import webview
except Exception as _webview_err:  # ImportError or a missing native backend
    webview = None
    _WEBVIEW_ERROR = _webview_err

logger = logging.getLogger("gtoolbox.desktop")


def find_available_port(start_port: int = 8000, max_attempts: int = 20, host: str = "127.0.0.1") -> int:
    """Finds an available TCP port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, port))
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


def setup_native_icon(window, window_title: str, ico_path: Path):
    """Safely applies native G-Toolbox icon to Win32 window and taskbar after window is shown."""
    if sys.platform != "win32" or not ico_path.exists():
        return

    def _on_shown():
        def _apply():
            time.sleep(0.4)
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

                for _ in range(20):
                    hwnd = ctypes.windll.user32.FindWindowW(None, window_title)
                    if hwnd:
                        ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, h_icon)
                        ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, h_icon)
                        break
                    time.sleep(0.2)
            except Exception:
                pass

        threading.Thread(target=_apply, daemon=True).start()

    window.events.shown += _on_shown


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


def install_save_dialog_hook(window):
    """Routes backend "Save As" requests to pywebview's native dialog."""
    save_mode = getattr(getattr(webview, "FileDialog", None), "SAVE", None)
    if save_mode is None:
        save_mode = getattr(webview, "SAVE_DIALOG", 30)

    def _dialog(initial_filename: str, ext: str):
        file_types = (f"{ext.upper()} (*.{ext})", "All files (*.*)") if ext else ("All files (*.*)",)
        result = window.create_file_dialog(save_mode, save_filename=initial_filename, file_types=file_types)
        if not result:
            return "CANCELED"
        return result[0] if isinstance(result, (list, tuple)) else str(result)

    dialogs.NATIVE_SAVE_DIALOG_HOOK = _dialog


def start_server():
    """Starts the API in a background thread; returns (url, thread)."""
    # Loopback only unless LAN pairing was explicitly enabled.
    bind_host = "0.0.0.0" if lan_access_enabled() else "127.0.0.1"
    port = find_available_port(start_port=8000, host=bind_host)
    server_url = f"http://127.0.0.1:{port}"

    cleanup_ready_flag()
    print(f"[*] Starting G-Toolbox backend on {bind_host}:{port}...")
    server_thread = ServerThread(app, host=bind_host, port=port)
    server_thread.start()

    print("[*] Waiting for backend to initialize...")
    if not wait_for_server(server_url, timeout=15.0):
        print("[-] Warning: Backend initialization took longer than expected. Proceeding...")
    notify_ready()  # tells the Windows launcher's splash screen to close
    return server_url, server_thread


def run_webview(server_url: str) -> bool:
    """Full app in a native window (pywebview). False if no backend could start."""
    window_title = "G-Toolbox — All-in-One Media & AI Studio"
    favicon_path = APP_DIR / "static" / "favicon.ico"
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
    setup_native_icon(window, window_title, favicon_path)
    install_save_dialog_hook(window)
    try:
        # Edge Chromium (WebView2) on Windows, WebKitGTK on Linux
        webview.start(gui="edgechromium" if sys.platform == "win32" else "gtk", debug=False)
        return True
    except Exception as e:
        print(f"[*] Native window failed ({e}).")
        dialogs.NATIVE_SAVE_DIALOG_HOOK = None
        return False


def _open_in_browser(url: str) -> None:
    # In a thread: on systems whose only browser is a console one, webbrowser
    # would block the caller until it exits.
    import webbrowser
    threading.Thread(target=webbrowser.open, args=(url,), daemon=True).start()


def run_control_window(server_url: str, server_thread: ServerThread, open_browser: bool = True) -> bool:
    """Small native window used when the full webview is unavailable (e.g. the
    Linux AppImage): shows that G-Toolbox is running, opens it in the browser,
    hosts the "Save As" dialog, and stops the server when closed.
    Returns False if no window can be shown (no display / no Tk)."""
    try:
        import queue
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk(className="G-Toolbox")  # WM_CLASS matches StartupWMClass in the .desktop file
    except Exception as e:
        print(f"[*] No window system available ({e}).")
        return False

    lang = (os.environ.get("LC_ALL") or os.environ.get("LC_MESSAGES") or os.environ.get("LANG") or "").lower()
    tr = lang.startswith("tr")

    def t(tr_text: str, en_text: str) -> str:
        return tr_text if tr else en_text

    bg, fg, muted, accent, error = "#0f1117", "#e6edf3", "#8b949e", "#7c3aed", "#f85149"
    root.title("G-Toolbox")
    root.configure(bg=bg, padx=24, pady=20)
    root.resizable(False, False)
    try:
        icon = tk.PhotoImage(file=str(APP_DIR / "static" / "icon.png"))
        root.iconphoto(True, icon)
    except Exception:
        pass

    tk.Label(root, text=t("G-Toolbox çalışıyor", "G-Toolbox is running"), bg=bg, fg=fg,
             font=("TkDefaultFont", 15, "bold")).pack(anchor="w")
    status = tk.Label(root, bg=bg, fg=muted, wraplength=380, justify="left",
                      text=t("Uygulama tarayıcınızda açılır. Bu pencereyi kapatınca G-Toolbox da kapanır.",
                             "The app opens in your web browser. Closing this window stops G-Toolbox."))
    status.pack(anchor="w", pady=(6, 12))

    address = tk.Entry(root, width=34, relief="flat", bg="#161b22", fg=fg, readonlybackground="#161b22",
                       insertbackground=fg, highlightthickness=0)
    address.insert(0, server_url)
    address.configure(state="readonly")
    address.pack(anchor="w", fill="x", ipady=6)

    buttons = tk.Frame(root, bg=bg)
    buttons.pack(anchor="w", fill="x", pady=(14, 0))

    def quit_app():
        server_thread.stop()
        root.destroy()

    tk.Button(buttons, text=t("Tarayıcıda aç", "Open in browser"), command=lambda: _open_in_browser(server_url),
              bg=accent, fg="white", activebackground="#6d28d9", activeforeground="white",
              relief="flat", padx=14, pady=6).pack(side="left")
    tk.Button(buttons, text=t("Kapat", "Quit"), command=quit_app, bg="#21262d", fg=fg,
              activebackground="#30363d", activeforeground=fg, relief="flat", padx=14, pady=6).pack(side="left", padx=(8, 0))
    root.protocol("WM_DELETE_WINDOW", quit_app)

    # "Save As" requests arrive on server threads; Tk may only be used from this
    # thread, so they are queued here and answered from the event loop.
    requests: "queue.Queue" = queue.Queue()

    def save_dialog_hook(initial_filename: str, ext: str):
        done, answer = threading.Event(), {}
        requests.put((initial_filename, ext, done, answer))
        if not done.wait(timeout=900):
            return "CANCELED"
        return answer.get("path") or "CANCELED"

    server_failed = [False]

    def pump():
        while True:
            try:
                name, ext, done, answer = requests.get_nowait()
            except queue.Empty:
                break
            types = ([(ext.upper(), f"*.{ext}")] if ext else []) + [(t("Tüm dosyalar", "All files"), "*")]
            root.deiconify()
            root.lift()
            answer["path"] = filedialog.asksaveasfilename(parent=root, initialfile=name, filetypes=types,
                                                         defaultextension=f".{ext}" if ext else "")
            done.set()
        if not server_thread.is_alive() and not server_failed[0]:
            server_failed[0] = True
            status.configure(fg=error, text=t(f"Sunucu durdu. Ayrıntılar: {LOG_DIR / 'desktop.log'}",
                                              f"The server stopped. Details: {LOG_DIR / 'desktop.log'}"))
        root.after(150, pump)

    dialogs.NATIVE_SAVE_DIALOG_HOOK = save_dialog_hook
    root.after(150, pump)
    if open_browser:
        root.after(300, lambda: _open_in_browser(server_url))
    print("[*] Control window shown; the app runs in the browser.")
    try:
        root.mainloop()
    finally:
        dialogs.NATIVE_SAVE_DIALOG_HOOK = None
    return True


def main():
    open_browser = "--no-browser" not in sys.argv
    server_url, server_thread = start_server()
    try:
        if webview is not None and run_webview(server_url):
            return
        if webview is None:
            print(f"[*] Native webview unavailable ({_WEBVIEW_ERROR}).")
        if run_control_window(server_url, server_thread, open_browser=open_browser):
            return
        # No window system at all: keep serving, open the browser if possible.
        print(f"[*] G-Toolbox is running at {server_url}")
        if open_browser:
            _open_in_browser(server_url)
        server_thread.join()
    finally:
        print("[*] Shutting down server...")
        cleanup_ready_flag()
        server_thread.stop()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        err_msg = traceback.format_exc()
        try:
            (LOG_DIR / "desktop_error.log").write_text(err_msg, encoding="utf-8")
        except Exception:
            pass
        raise
