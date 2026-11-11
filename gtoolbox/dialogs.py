"""Native 'Save As' dialog on the host computer (pywebview hook, PowerShell, Tk)."""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

from .config import logger


# Set by desktop_app.py: callable(initial_filename, ext) -> path | "CANCELED" | None
NATIVE_SAVE_DIALOG_HOOK = None


_SAFE_EXT_RE = re.compile(r"^[A-Za-z0-9]{1,10}$")


def _clean_dialog_inputs(initial_filename: str, file_ext: str) -> tuple[str, str]:
    """Reduces dialog inputs to a bare file name and an alphanumeric extension."""
    name = Path(str(initial_filename or "")).name.strip() or "file"
    name = re.sub(r'[\x00-\x1f<>:"/\\|?*]', "_", name)[:200]
    ext = str(file_ext or "").lstrip(".")
    if not _SAFE_EXT_RE.match(ext):
        ext = ""
    return name, ext


def _open_native_save_dialog(initial_filename: str, file_ext: str = "") -> Optional[str]:
    """Opens a native Save As dialog on the host computer.

    Returns the chosen absolute path, "CANCELED", or None if no dialog is available.
    User-controlled values are never interpolated into a command line.
    """
    initial_filename, clean_ext = _clean_dialog_inputs(initial_filename, file_ext)

    # 0. Desktop window (pywebview) provides its own native dialog.
    if NATIVE_SAVE_DIALOG_HOOK is not None:
        try:
            return NATIVE_SAVE_DIALOG_HOOK(initial_filename, clean_ext)
        except Exception as e:
            logger.warning(f"pywebview save dialog failed: {e}")

    # 1. Windows: WinForms SaveFileDialog via PowerShell. The script is constant;
    #    file name and filter are passed through environment variables.
    if sys.platform == "win32":
        try:
            filter_str = f"{clean_ext.upper()} Files (*.{clean_ext})|*.{clean_ext}|All Files (*.*)|*.*" if clean_ext else "All Files (*.*)|*.*"
            ps_cmd = (
                "[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms') | Out-Null; "
                "$f = New-Object System.Windows.Forms.SaveFileDialog; "
                "$f.FileName = $env:GT_SAVE_NAME; "
                "$f.Filter = $env:GT_SAVE_FILTER; "
                "$f.Title = 'G-Toolbox'; "
                "$top = New-Object System.Windows.Forms.Form; "
                "$top.TopMost = $true; "
                "if ($f.ShowDialog($top) -eq [System.Windows.Forms.DialogResult]::OK) { "
                "Write-Output $f.FileName "
                "} else { Write-Output '__CANCELED__' }"
            )
            env = dict(os.environ, GT_SAVE_NAME=initial_filename, GT_SAVE_FILTER=filter_str)
            res = subprocess.run(
                ["powershell", "-Sta", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=180,
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            out_str = res.stdout.strip()
            if out_str == "__CANCELED__":
                return "CANCELED"
            if out_str and os.path.isabs(out_str):
                return out_str
        except Exception as e:
            logger.warning(f"PowerShell SaveFileDialog exception: {e}")

    # 2. Secondary fallback: Tkinter (if available on standard Python distros)
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        types = []
        if clean_ext:
            types.append((f"{clean_ext.upper()} Dosyaları (*.{clean_ext})", f"*.{clean_ext}"))
        types.append(("Tüm Dosyalar (*.*)", "*.*"))

        chosen_path = filedialog.asksaveasfilename(
            parent=root,
            initialfile=initial_filename,
            defaultextension=f".{clean_ext}" if clean_ext else None,
            filetypes=types,
            title="G-Toolbox — Dosyayı Farklı Kaydet"
        )
        root.destroy()
        return chosen_path if chosen_path else "CANCELED"
    except Exception as e:
        logger.debug(f"Tkinter dialog fallback: {e}")

    # If GUI dialog cannot be opened on this OS, return None to trigger browser stream download
    return None
