"""Local AI engines: model registry (hash-pinned), runtime loading, setup and caches.

Mutable state (loaded libraries, model caches, install progress) lives here;
other modules must access it as ``ai.<name>`` so they always see current values."""

import gc
import os
import socket
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

from .config import BASE_DIR, DATA_DIR, PIP_TARGET, logger
from .net import _safe_urlopen, sha256_file, verify_authenticode_microsoft


# Model file locations are resolved (and hash-verified) by find_verified_model().
os.environ.setdefault("TORCH_HOME", str(Path.home() / ".cache" / "torch"))


try:
    from rembg import remove as rembg_remove
    REMBG_AVAILABLE = True
except Exception:
    rembg_remove = None
    REMBG_AVAILABLE = False


def _patch_pillow_compatibility():
    """Patches PIL.Image.Image to restore backward-compatibility for AI libraries.
    Starting with Pillow 10.1.0+, Image.mode is a read-only property without a setter.
    Legacy AI libraries (rembg, u2net, basicsr, etc.) that assign img.mode directly throw:
    AttributeError: can't set attribute 'mode'.
    This patch safely restores the mode setter.
    """
    try:
        from PIL import Image
        try:
            test_im = Image.new("RGB", (1, 1))
            test_im.mode = "RGB"
        except (AttributeError, TypeError):
            fget = Image.Image.mode.fget
            def fset(self, value):
                self._mode = value
            Image.Image.mode = property(fget, fset)
            logger.info("🔧 Pillow Image.mode property setter backward-compatibility patch applied.")
    except Exception as e:
        logger.debug(f"Pillow compatibility patch notice: {e}")


_patch_pillow_compatibility()
_AI_INSTALL_PROGRESS = {
    "status": "idle",
    "progress": 0,
    "current_model": "",
    "error": None
}


# Pinned SHA-256 of every model file G-Toolbox downloads. A file that does not
# match is deleted and never loaded (.pth/.pt files are pickles: loading an
# unverified one is code execution).
MODEL_SHA256 = {
    "RealESRGAN_x4plus.pth": "4fa0d38905f75ac06eb49a7951b426670021be3018265fd191d2125df9d682f1",
    "RealESRGAN_x4plus_anime_6B.pth": "f872d837d3c90ed2e05227bed711af5671a6fd1c9f7d7e91c911a61f155e99da",
    "big-lama.pt": "7ba7aa7ac37a4d41fdbbeba3a2af7ead18058552997e3a3cd1a3b2210c9e6b4c",
    "u2net.onnx": "8d10d2f3bb75ae3b6d527c77944fc5e7dcd94b29809d47a739a7a728a912b491",
}


_VERIFIED_MODEL_FILES: set = set()


def verify_model_file(path: Path) -> bool:
    """True if `path` matches its pinned hash. Result is cached per process."""
    key = (str(path), path.stat().st_size if path.exists() else -1)
    if key in _VERIFIED_MODEL_FILES:
        return True
    expected = MODEL_SHA256.get(path.name)
    if not expected or not path.exists():
        return False
    ok = sha256_file(path) == expected
    if ok:
        _VERIFIED_MODEL_FILES.add(key)
    else:
        logger.error(f"Integrity check failed for {path} (unexpected SHA-256).")
    return ok


# name -> (download URL, default destination, extra locations searched for an existing copy)
MODEL_REGISTRY = {
    "RealESRGAN_x4plus.pth": (
        "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
        DATA_DIR / "RealESRGAN_x4plus.pth", [BASE_DIR / "RealESRGAN_x4plus.pth"],
    ),
    "RealESRGAN_x4plus_anime_6B.pth": (
        "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth",
        DATA_DIR / "RealESRGAN_x4plus_anime_6B.pth", [BASE_DIR / "RealESRGAN_x4plus_anime_6B.pth"],
    ),
    "big-lama.pt": (
        "https://github.com/enesmsahin/simple-lama-inpainting/releases/download/v0.1.0/big-lama.pt",
        Path.home() / ".cache" / "torch" / "hub" / "checkpoints" / "big-lama.pt",
        [BASE_DIR / "big-lama.pt"],
    ),
    "u2net.onnx": (
        "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx",
        Path.home() / ".u2net" / "u2net.onnx",
        [BASE_DIR / "u2net.onnx"],
    ),
}


def model_candidates(name: str) -> list:
    _, default_dest, extra = MODEL_REGISTRY[name]
    return list(extra) + [default_dest]


def find_verified_model(name: str) -> Optional[Path]:
    """Returns the first existing copy of `name` whose SHA-256 matches, else None."""
    for cand in model_candidates(name):
        if cand.exists() and verify_model_file(cand):
            return cand
    return None


def ensure_model(name: str, pct_start: int = 0, pct_end: int = 100, label: Optional[str] = None) -> Path:
    """Returns a verified copy of the model, downloading it if needed."""
    found = find_verified_model(name)
    if found:
        return found
    url, dest, _ = MODEL_REGISTRY[name]
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest.unlink()  # present but failed verification
    _download_chunked_file(url, dest, 1, pct_start, pct_end, label or name)
    if not verify_model_file(dest):
        raise RuntimeError(f"{name} failed integrity verification after download.")
    return dest


SimpleLama = None
LAMA_AVAILABLE = False
_LAMA_INSTANCE = None
_REMBG_SESSION = None
cv2 = None
np = None
torch = None
RRDBNet = None
RealESRGANer = None
_UPSCALER_INSTANCE = None
_UPSCALER_INSTANCES = {}


def _unblock_directory(dir_path: Path):
    """Recursively removes Zone.Identifier alternate data streams (Mark of the Web) from files."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        del_file = ctypes.windll.kernel32.DeleteFileW
        if dir_path.is_file():
            del_file(str(dir_path) + ":Zone.Identifier")
            return
        if not dir_path.exists():
            return
        for f in dir_path.rglob("*"):
            if f.is_file():
                try:
                    del_file(str(f) + ":Zone.Identifier")
                except Exception:
                    pass
    except Exception as e:
        logger.debug(f"Unblock notice: {e}")


def _is_vc_redist_installed() -> bool:
    """Checks if Microsoft Visual C++ 2015-2022 Redistributable (x64) is installed."""
    if sys.platform != "win32":
        return True
    try:
        sys_dir = Path(os.environ.get("SystemRoot", "C:\\Windows")) / "System32"
        vc140_1 = sys_dir / "vcruntime140_1.dll"
        msvcp140 = sys_dir / "msvcp140.dll"
        if vc140_1.exists() and msvcp140.exists():
            return True
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\X64")
        val, _ = winreg.QueryValueEx(key, "Installed")
        return bool(val == 1)
    except Exception:
        return False


def _ensure_vc_redist() -> bool:
    """Ensures Microsoft Visual C++ 2015-2022 Redistributable is installed; downloads and runs installer if missing."""
    if sys.platform != "win32" or _is_vc_redist_installed():
        return True
    try:
        import tempfile
        vc_url = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
        vc_tmp = Path(tempfile.gettempdir()) / "vc_redist.x64.exe"
        logger.info("Downloading Microsoft Visual C++ 2015-2022 Redistributable (x64)...")
        req = urllib.request.Request(vc_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) G-Toolbox/4.4"})
        with _safe_urlopen(req, timeout=180) as resp, open(vc_tmp, "wb") as f:
            f.write(resp.read())

        if not verify_authenticode_microsoft(vc_tmp):
            vc_tmp.unlink(missing_ok=True)
            logger.error("vc_redist.x64.exe is not validly signed by Microsoft; refusing to run it.")
            return False

        logger.info("Installing Microsoft Visual C++ Redistributable...")
        cmd = [str(vc_tmp), "/install", "/quiet", "/norestart"]
        res = subprocess.run(cmd, timeout=180)
        try:
            vc_tmp.unlink()
        except Exception:
            pass
        return res.returncode in (0, 3010)
    except Exception as e:
        logger.warning(f"Could not auto-install VC++ Redistributable: {e}")
        return False


def _register_dll_directories():
    """Registers potential native DLL directories for Windows Python 3.8+ to prevent DLL load failed errors."""
    if sys.platform != "win32":
        return

    sp_candidates = []
    for p in sys.path:
        p_obj = Path(p)
        if p_obj.is_dir() and "site-packages" in p_obj.parts and p_obj not in sp_candidates:
            sp_candidates.append(p_obj)

    runtime_sp = BASE_DIR / "runtime" / "Lib" / "site-packages"
    if runtime_sp.exists() and runtime_sp not in sp_candidates:
        sp_candidates.append(runtime_sp)

    dll_subdirs = [
        Path("torch") / "lib",
        Path("onnxruntime") / "capi",
        Path("cv2"),
        Path("scipy") / ".libs",
        Path("PIL") / ".libs",
    ]

    added_dirs = set()
    for sp in sp_candidates:
        for subdir in dll_subdirs:
            target = sp / subdir
            if target.is_dir():
                target_str = str(target.resolve())
                if target_str not in added_dirs:
                    added_dirs.add(target_str)
                    _unblock_directory(target)
                    if hasattr(os, "add_dll_directory"):
                        try:
                            os.add_dll_directory(target_str)
                        except Exception:
                            pass
                    if target_str not in os.environ.get("PATH", ""):
                        os.environ["PATH"] = target_str + os.path.pathsep + os.environ.get("PATH", "")


def ensure_ai_runtime() -> bool:
    """Dynamically verifies and imports AI frameworks (Torch, RealESRGAN, BasicSR, Rembg, LaMa, Whisper, Demucs).
    Ensures hotfixes are applied and libraries installed during app runtime are immediately accessible without restart.
    """
    global torch, cv2, np, RRDBNet, RealESRGANer, SimpleLama, LAMA_AVAILABLE, rembg_remove, REMBG_AVAILABLE

    import importlib
    importlib.invalidate_caches()

    # 0. Ensure runtime/Lib/site-packages is present in sys.path (critical for portable Python)
    try:
        runtime_sp = BASE_DIR / "runtime" / "Lib" / "site-packages"
        if runtime_sp.exists() and str(runtime_sp) not in sys.path:
            sys.path.insert(0, str(runtime_sp))
        _register_dll_directories()
    except Exception:
        pass

    # 0.1 Ensure Pillow Image.mode setter is active
    _patch_pillow_compatibility()

    # 1. Hotfix: basicsr requires torchvision.transforms.functional_tensor
    try:
        importlib.import_module("torchvision.transforms.functional_tensor")  # availability probe
    except ImportError:
        try:
            import torchvision.transforms.functional as functional
            sys.modules['torchvision.transforms.functional_tensor'] = functional
        except Exception:
            pass

    # 2. PyTorch & RealESRGAN
    if RealESRGANer is None or torch is None:
        try:
            import torch as _t
            import cv2 as _c
            import numpy as _n
            from basicsr.archs.rrdbnet_arch import RRDBNet as _RRDBNet
            from realesrgan import RealESRGANer as _RealESRGANer

            torch = _t
            cv2 = _c
            np = _n
            RRDBNet = _RRDBNet
            RealESRGANer = _RealESRGANer
            logger.info("✅ RealESRGAN & PyTorch runtime loaded successfully.")
        except Exception as e:
            err_msg = str(e)
            if "4551" in err_msg or "c10.dll" in err_msg or "application control" in err_msg.lower() or "uygulama denetimi" in err_msg.lower():
                logger.error(
                    "❌ [WinError 4551] Windows Application Control (Smart App Control) blocked torch/lib/c10.dll or its dependencies. "
                    "Remedies: 1) Run G-Toolbox as Administrator. "
                    "2) In Windows Security -> App & browser control -> Smart App Control -> set to Off."
                )
            else:
                logger.debug(f"AI upscaler dynamic load: {e}")

    # 3. Rembg
    if not REMBG_AVAILABLE or rembg_remove is None:
        try:
            from rembg import remove as _rembg_remove
            rembg_remove = _rembg_remove
            REMBG_AVAILABLE = True
            logger.info("✅ Rembg runtime loaded successfully.")
        except Exception as e:
            logger.warning(f"Rembg dynamic load: {e}")

    # 4. SimpleLama
    if not LAMA_AVAILABLE or SimpleLama is None:
        try:
            from simple_lama_inpainting import SimpleLama as _SimpleLama
            SimpleLama = _SimpleLama
            LAMA_AVAILABLE = True
            logger.info("✅ SimpleLama runtime loaded successfully.")
        except Exception as e:
            logger.debug(f"SimpleLama dynamic load: {e}")

    return bool(torch and RealESRGANer)


# Initial load attempt on server startup
try:
    ensure_ai_runtime()
except Exception as _e:
    logger.debug(f"Initial AI runtime check notice: {_e}")


def get_rembg_session():
    """Returns singleton rembg session for u2net to avoid reloading and reallocating ONNX graph per request."""
    global _REMBG_SESSION
    if _REMBG_SESSION is None:
        ensure_ai_runtime()
        if not REMBG_AVAILABLE or rembg_remove is None:
            raise RuntimeError("rembg library is not installed yet. Please complete AI setup.")
        u2_path = find_verified_model("u2net.onnx")
        if u2_path is None:
            raise RuntimeError("U2-Net model is missing or failed verification. Please run AI setup.")
        os.environ["U2NET_HOME"] = str(u2_path.parent)
        from rembg import new_session
        _REMBG_SESSION = new_session("u2net")
    return _REMBG_SESSION


def get_lama_model():
    global _LAMA_INSTANCE
    if _LAMA_INSTANCE is None:
        ensure_ai_runtime()
        if not LAMA_AVAILABLE or SimpleLama is None:
            raise RuntimeError("simple-lama-inpainting library is not installed yet. Please complete AI setup.")
        lama_path = find_verified_model("big-lama.pt")
        if lama_path is None:
            raise RuntimeError("LaMa model is missing or failed verification. Please run AI setup.")
        # SimpleLama would otherwise download an unverified checkpoint itself.
        os.environ["LAMA_MODEL"] = str(lama_path)
        _LAMA_INSTANCE = SimpleLama()
    return _LAMA_INSTANCE


def get_upscaler(model_type: str = "general", force_fp32: bool = False):
    global _UPSCALER_INSTANCE
    ensure_ai_runtime()
    if RealESRGANer is None:
        raise RuntimeError("realesrgan or PyTorch is not installed yet. Please complete AI setup.")

    m_key = "anime" if "anime" in str(model_type).lower() else "general"
    cache_key = f"{m_key}_fp32" if force_fp32 else m_key

    # Return cached singleton if already loaded and not forcing FP32 fallback
    if cache_key in _UPSCALER_INSTANCES and not force_fp32:
        return _UPSCALER_INSTANCES[cache_key]

    if m_key == "anime":
        model_name = "RealESRGAN_x4plus_anime_6B.pth"
        num_block = 6
    else:
        model_name = "RealESRGAN_x4plus.pth"
        num_block = 23

    # Hash-verified (downloads and verifies if missing or tampered)
    model_path = ensure_model(model_name)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=num_block, num_grow_ch=32, scale=4)
    
    # Half-precision (FP16) produces NaN / black images on GTX 16xx Turing and older Pascal cards
    half = False
    if torch.cuda.is_available() and not force_fp32:
        try:
            gpu_name = torch.cuda.get_device_name(0).lower()
            if not any(x in gpu_name for x in ["1650", "1660", "gtx 10", "gtx 9"]):
                half = True
        except Exception:
            half = False

    tile_size = 256 if (torch.cuda.is_available() and half) else 192

    upscaler_model = RealESRGANer(
        scale=4,
        model_path=str(model_path),
        model=model,
        tile=tile_size,
        tile_pad=10,
        pre_pad=0,
        half=half,
        device=device
    )

    if not force_fp32:
        _UPSCALER_INSTANCES[cache_key] = upscaler_model
        _UPSCALER_INSTANCE = upscaler_model
    return upscaler_model


def check_ai_models_status() -> dict:
    """Checks the status and presence of local AI model weights and runtime availability."""
    ensure_ai_runtime()

    models = {
        "realesrgan_general": {
            "name": "Real-ESRGAN (General 4x)",
            "installed": False,
            "size_mb": 67.0,
        },
        "realesrgan_anime": {
            "name": "Real-ESRGAN (Anime 4x)",
            "installed": False,
            "size_mb": 17.9,
        },
        "lama": {
            "name": "LaMa Magic Eraser",
            "installed": False,
            "size_mb": 198.0,
        },
        "u2net": {
            "name": "U2-Net Background Remover",
            "installed": False,
            "size_mb": 176.0,
        },
    }

    # Each model counts as installed only if a copy passes SHA-256 verification.
    gen_path = find_verified_model("RealESRGAN_x4plus.pth")
    ani_path = find_verified_model("RealESRGAN_x4plus_anime_6B.pth")
    lama_path = find_verified_model("big-lama.pt")
    u2_path = find_verified_model("u2net.onnx")
    torch_ok = torch is not None and RealESRGANer is not None
    models["realesrgan_general"]["installed"] = bool(gen_path and torch_ok)
    models["realesrgan_anime"]["installed"] = bool(ani_path and torch_ok)
    models["lama"]["installed"] = bool(lama_path and LAMA_AVAILABLE and SimpleLama is not None)
    models["u2net"]["installed"] = bool(u2_path and REMBG_AVAILABLE and rembg_remove is not None)

    all_installed = all(m["installed"] for m in models.values())
    essential_installed = (
        models["realesrgan_general"]["installed"]
        and models["u2net"]["installed"]
        and models["lama"]["installed"]
    )

    return {
        "success": True,
        "models": models,
        "all_installed": all_installed,
        "essential_installed": essential_installed,
        "torch_cuda_available": bool(torch.cuda.is_available()) if torch else False,
        "rembg_available": bool(REMBG_AVAILABLE and rembg_remove is not None),
        "torch_available": bool(torch is not None and RealESRGANer is not None),
        "lama_available": bool(LAMA_AVAILABLE and SimpleLama is not None),
    }


def _run_pip_step(args: list, step_label: str, pct: int):
    """Executes a pip command safely with extended timeout and live progress reporting."""
    _AI_INSTALL_PROGRESS["current_model"] = step_label
    _AI_INSTALL_PROGRESS["progress"] = pct
    py_exe = sys.executable
    if PIP_TARGET and args and args[0] == "install":
        args = args + ["--target", PIP_TARGET, "--upgrade"]
    cmd = [
        py_exe, "-m", "pip"
    ] + args + [
        "--no-input",
        "--no-warn-script-location",
        "--prefer-binary",
        "--default-timeout", "180",
        "--retries", "5"
    ]
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        try:
            out, err = proc.communicate(timeout=900)
            if proc.returncode != 0:
                err_clean = (err or out or "Unknown pip error").strip()
                logger.error(f"Pip command failed ({step_label}) [code {proc.returncode}]: {err_clean}")
                raise RuntimeError(f"Pip error during '{step_label}': {err_clean[-300:]}")
        except subprocess.TimeoutExpired:
            proc.kill()
            logger.error(f"Pip command timed out: {step_label}")
            raise RuntimeError(f"Pip timed out during '{step_label}'. Please check network.")
    except Exception as ex:
        logger.error(f"Pip execution error ({step_label}): {ex}")
        raise ex


def _download_chunked_file(url: str, dest_path: Path, expected_min_size: int, pct_start: int, pct_end: int, label: str):
    """Downloads large model weights in chunks with auto-resume (HTTP Range) and retry resilience against timeouts."""
    tmp_path = dest_path.with_suffix(dest_path.suffix + ".tmp")

    max_retries = 5
    retry_delay = 2.0
    chunk_size = 256 * 1024  # 256 KB chunks for smoother updates and faster recovery
    total_size = 0

    for attempt in range(1, max_retries + 1):
        try:
            downloaded = tmp_path.stat().st_size if tmp_path.exists() else 0

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }

            if downloaded > 0:
                headers["Range"] = f"bytes={downloaded}-"

            req = urllib.request.Request(url, headers=headers)

            with _safe_urlopen(req, timeout=180) as resp:
                status_code = getattr(resp, "status", 200)
                content_len = resp.headers.get("Content-Length")
                content_range = resp.headers.get("Content-Range")

                if status_code == 206:
                    # Partial content: server accepted byte range
                    if content_range and "/" in content_range:
                        try:
                            range_total = int(content_range.split("/")[-1])
                            if range_total > 0:
                                total_size = range_total
                        except Exception:
                            pass
                    if total_size == 0 and content_len and content_len.isdigit():
                        total_size = downloaded + int(content_len)
                    file_mode = "ab"
                else:
                    # 200 OK: server sent full file or range unsupported
                    if content_len and content_len.isdigit():
                        total_size = int(content_len)
                    downloaded = 0
                    file_mode = "wb"

                total_mb = total_size / (1024 * 1024) if total_size > 0 else 0

                with open(tmp_path, file_mode) as f:
                    while True:
                        try:
                            chunk = resp.read(chunk_size)
                        except (socket.timeout, TimeoutError, ssl.SSLError) as read_err:
                            logger.warning(f"Chunk read timeout on {label} at {downloaded / (1024 * 1024):.1f} MB: {read_err}")
                            raise read_err

                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        dl_mb = downloaded / (1024 * 1024)

                        if total_size > 0:
                            ratio = min(1.0, downloaded / total_size)
                            curr_pct = int(pct_start + ratio * (pct_end - pct_start))
                            _AI_INSTALL_PROGRESS["current_model"] = f"{label} ({dl_mb:.1f} / {total_mb:.1f} MB - {int(ratio * 100)}%)"
                            _AI_INSTALL_PROGRESS["progress"] = min(99, max(pct_start, curr_pct))
                        else:
                            _AI_INSTALL_PROGRESS["current_model"] = f"{label} ({dl_mb:.1f} MB downloaded...)"

            # Successful stream completion
            actual_size = tmp_path.stat().st_size if tmp_path.exists() else 0
            if actual_size >= expected_min_size:
                expected_sha = MODEL_SHA256.get(dest_path.name)
                if expected_sha:
                    _AI_INSTALL_PROGRESS["current_model"] = f"{label} - verifying integrity..."
                    actual_sha = sha256_file(tmp_path)
                    if actual_sha != expected_sha:
                        tmp_path.unlink(missing_ok=True)
                        raise RuntimeError(
                            f"{label}: SHA-256 mismatch (got {actual_sha[:16]}…). "
                            "The download was corrupted or tampered with and has been discarded."
                        )
                tmp_path.replace(dest_path)
                logger.info(f"Successfully downloaded and verified {label} ({actual_size} bytes).")
                return
            else:
                logger.warning(f"{label} download size incomplete ({actual_size} < {expected_min_size}). Retrying...")
                if attempt == max_retries:
                    raise RuntimeError(f"{label} download incomplete ({actual_size} bytes, expected: {expected_min_size}).")

        except Exception as ex:
            err_msg = str(ex)
            is_network_err = (
                isinstance(ex, (socket.timeout, TimeoutError, urllib.error.URLError, ssl.SSLError))
                or "timed out" in err_msg.lower()
                or "timeout" in err_msg.lower()
                or "incomplete" in err_msg.lower()
                or "connection" in err_msg.lower()
            )
            if is_network_err and attempt < max_retries:
                dl_mb = (tmp_path.stat().st_size / (1024 * 1024)) if tmp_path.exists() else 0
                logger.warning(f"{label} connection timeout ({ex}). Retrying from ({dl_mb:.1f} MB) in {retry_delay:.1f}s (Attempt {attempt}/{max_retries})...")
                _AI_INSTALL_PROGRESS["current_model"] = f"{label} - Reconnecting (Resuming from: {dl_mb:.1f} MB, Attempt {attempt}/{max_retries})..."
                time.sleep(retry_delay)
                retry_delay = min(10.0, retry_delay * 1.5)
                continue
            elif attempt >= max_retries:
                if tmp_path.exists():
                    try:
                        tmp_path.unlink()
                    except Exception:
                        pass
                raise RuntimeError(f"Connection timed out while downloading {label} (5 attempts failed): {ex}") from ex
            else:
                raise ex


def _download_ai_models_worker():
    _AI_INSTALL_PROGRESS["status"] = "downloading"
    _AI_INSTALL_PROGRESS["error"] = None

    try:
        # 0. Check and install Visual C++ 2015-2022 Redistributable if missing
        if sys.platform == "win32" and not _is_vc_redist_installed():
            _AI_INSTALL_PROGRESS["current_model"] = "Installing Microsoft Visual C++ Redistributable..."
            _AI_INSTALL_PROGRESS["progress"] = 2
            _ensure_vc_redist()

        # 1. Check and install python AI libraries if missing
        ensure_ai_runtime()
        if torch is None or RealESRGANer is None:
            _run_pip_step(["install", "torch", "torchvision", "--index-url", "https://download.pytorch.org/whl/cpu"], "Installing PyTorch CPU (~250 MB, 1-3 min)...", 5)
            _run_pip_step(["install", "basicsr", "--no-deps"], "Configuring BasicSR architecture...", 15)
            _run_pip_step(["install", "realesrgan"], "Installing RealESRGAN...", 20)

        if not REMBG_AVAILABLE or rembg_remove is None or not LAMA_AVAILABLE or SimpleLama is None:
            _run_pip_step(["install", "rembg", "simple-lama-inpainting", "faster-whisper", "demucs"], "Installing AI libraries (Rembg, LaMa, Whisper, Demucs)...", 24)

        # Invalidate import caches, register DLLs, and unblock directory
        import importlib
        importlib.invalidate_caches()
        ensure_ai_runtime()

        # 2-5. Model weights: downloaded over verified TLS and checked against pinned SHA-256
        ensure_model("RealESRGAN_x4plus.pth", 28, 48, "Real-ESRGAN General")
        _AI_INSTALL_PROGRESS["progress"] = max(_AI_INSTALL_PROGRESS["progress"], 48)
        ensure_model("RealESRGAN_x4plus_anime_6B.pth", 48, 62, "Real-ESRGAN Anime")
        _AI_INSTALL_PROGRESS["progress"] = max(_AI_INSTALL_PROGRESS["progress"], 62)
        ensure_model("big-lama.pt", 62, 82, "LaMa Object Remover")
        _AI_INSTALL_PROGRESS["progress"] = max(_AI_INSTALL_PROGRESS["progress"], 82)
        ensure_model("u2net.onnx", 82, 98, "U2-Net Background Remover")
        _AI_INSTALL_PROGRESS["progress"] = max(_AI_INSTALL_PROGRESS["progress"], 98)

        ensure_ai_runtime()
        missing = []
        if not REMBG_AVAILABLE or rembg_remove is None:
            missing.append("rembg (Background Remover)")
        if torch is None or RealESRGANer is None:
            missing.append("torch / RealESRGAN (Upscaler)")
        if not LAMA_AVAILABLE or SimpleLama is None:
            missing.append("simple-lama-inpainting (Magic Eraser)")
        if missing:
            raise RuntimeError(f"AI kütüphaneleri eksik veya başlatılamadı: {', '.join(missing)}. Lütfen yönetici olarak yeniden başlatın veya internet bağlantınızı kontrol edin.")

        _AI_INSTALL_PROGRESS["progress"] = 100
        _AI_INSTALL_PROGRESS["status"] = "done"
        _AI_INSTALL_PROGRESS["current_model"] = "All AI Models Ready!"
    except Exception as e:
        logger.error(f"AI model download failed: {e}")
        _AI_INSTALL_PROGRESS["status"] = "error"
        err_msg = str(e)
        if "4551" in err_msg or "c10.dll" in err_msg or "application control" in err_msg.lower() or "uygulama denetimi" in err_msg.lower():
            _AI_INSTALL_PROGRESS["error"] = (
                "[WinError 4551] Windows Application Control (Smart App Control) blocked torch/lib/c10.dll or its dependencies. "
                "Remedies: 1) Run G-Toolbox as Administrator. "
                "2) If Windows 11 Smart App Control is active, set it to Off in Windows Security (App & browser control -> Smart App Control -> Off)."
            )
        else:
            _AI_INSTALL_PROGRESS["error"] = err_msg


def start_ai_install() -> bool:
    """Starts the background AI setup. False if one is already running."""
    global _AI_INSTALL_PROGRESS
    if _AI_INSTALL_PROGRESS["status"] == "downloading":
        return False
    _AI_INSTALL_PROGRESS = {
        "status": "downloading",
        "progress": 5,
        "current_model": "Preparing...",
        "error": None
    }
    import threading
    threading.Thread(target=_download_ai_models_worker, daemon=True).start()
    return True


def delete_ai_model_files() -> tuple:
    """Deletes every downloaded model file; returns (freed_mb, deleted_file_names)."""
    freed_bytes = 0
    deleted_files = []

    # Every location a model may live in, plus partial downloads
    target_paths = []
    for name in MODEL_REGISTRY:
        for cand in model_candidates(name):
            target_paths += [cand, cand.with_suffix(cand.suffix + ".tmp")]
    target_paths = list(dict.fromkeys(target_paths))

    for p in target_paths:
        if p.exists():
            try:
                size = p.stat().st_size
                p.unlink()
                freed_bytes += size
                deleted_files.append(p.name)
            except Exception as e:
                logger.error(f"Failed to delete {p}: {e}")

    freed_mb = round(freed_bytes / (1024 * 1024), 1)
    logger.info(f"Deleted local AI models. Freed {freed_mb} MB.")
    return freed_mb, deleted_files


# ── Faster-Whisper Local Transcription ────────────────────────────
_WHISPER_MODELS: dict[str, object] = {}


WHISPER_ALLOWED_MODELS = {
    "tiny", "tiny.en", "base", "base.en", "small", "small.en",
    "medium", "medium.en", "large-v2", "large-v3", "turbo", "large-v3-turbo",
}


def get_whisper_model(model_size: str = "base"):
    key = str(model_size).lower().strip() or "base"
    if key not in WHISPER_ALLOWED_MODELS:
        raise ValueError(f"Unsupported Whisper model: {key}")
    ensure_ai_runtime()
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise RuntimeError("faster-whisper library is not installed.")

    if key not in _WHISPER_MODELS:
        # Keep at most one Whisper model in memory.
        _WHISPER_MODELS.clear()
        gc.collect()
        device = "cuda" if (torch and torch.cuda.is_available()) else "cpu"
        compute_type = "float16" if (torch and torch.cuda.is_available()) else "int8"
        _WHISPER_MODELS[key] = WhisperModel(key, device=device, compute_type=compute_type)
    return _WHISPER_MODELS[key]


# ── Hardware Telemetry & VRAM Management ─────────────────────────
def purge_vram_and_models():
    """Unloads cached AI models (RealESRGAN, LaMa, Rembg, Faster-Whisper) and purges CUDA/RAM cache."""
    global _UPSCALER_INSTANCE, _LAMA_INSTANCE, _REMBG_SESSION
    _UPSCALER_INSTANCE = None
    _UPSCALER_INSTANCES.clear()
    _LAMA_INSTANCE = None
    _REMBG_SESSION = None
    _WHISPER_MODELS.clear()
    
    import gc
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
    except Exception:
        pass
    logger.info("🧹 Purged all cached AI models and released VRAM/RAM.")
