# ⚡ G-Toolbox — Local AI & Media Toolkit

[![Release](https://img.shields.io/github/v/release/Gorkem-Taha/G-Toolbox?color=success)](https://github.com/Gorkem-Taha/G-Toolbox/releases/latest)
[![Tests](https://github.com/Gorkem-Taha/G-Toolbox/actions/workflows/tests.yml/badge.svg)](https://github.com/Gorkem-Taha/G-Toolbox/actions/workflows/tests.yml)
![License](https://img.shields.io/badge/license-CC%20BY--NC%204.0-red.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20Android-lightgrey.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)

G-Toolbox is an all-in-one workspace for media, documents and local AI. Your files are
processed on your own computer: nothing is uploaded to a cloud service and no account or
API key is needed. A phone can use the computer's power over your Wi-Fi after a one-time
pairing.

> ⚠️ **Non-commercial license.** G-Toolbox is licensed under
> [CC BY-NC 4.0](LICENSE): free for personal and educational use. Commercial use requires
> a separate license from the author.

![G-Toolbox home](./static/menu.png?v=2)

---

## 🧰 Tools

| Tool | What it does | Engine |
| :--- | :--- | :--- |
| 🔄 Media converter | Image, audio and video format conversion | Pillow, FFmpeg |
| ✂️ Background remover | Cuts out the main subject as a transparent PNG | U²-Net (rembg) |
| 🪄 Magic eraser | Removes painted objects, text or watermarks | LaMa |
| 🌌 Upscaler | 2× / 4× super-resolution, photo and anime models, keeps transparency | Real-ESRGAN |
| 📥 Video downloader | Downloads video or MP3 from YouTube and other sites | yt-dlp, FFmpeg |
| 🔒 Vault | Encrypts a file or a folder into an AES-256 `.enc` archive | pyAesCrypt (AES Crypt format) |
| 🎙️ Vocal separator | Vocals / instrumental or 4 stems, as a zip | Demucs (htdemucs) |
| 📝 Transcriber | Speech to text: TXT, SRT, WebVTT or JSON | faster-whisper |
| 🛡️ Metadata cleaner | Shows and removes EXIF/GPS/XMP/comments; keeps pixels, palette, animation and JPEG quality | Pillow |
| 🎬 GIF / WebP maker | Clip → animated GIF (palette-optimised) or WebP | FFmpeg |
| 💬 Subtitle burner | Burns SRT/VTT/ASS subtitles into a video | FFmpeg (libass) |
| 📄 PDF toolkit | Merge, extract page ranges (`1-3, 5, 8-`), extract text | pypdf |
| 🎚️ Audio effects | Slowed + reverb, nightcore, tempo and pitch | FFmpeg |
| 🧹 Noise cleaner | FFT noise reduction with optional voice focus, audio or video | FFmpeg (afftdn) |

AI tools need the **AI engines**, which are installed on demand from the app (see below).
Everything else works right after installation.

---

## 🔒 Privacy and security model

- **Local by default.** The server listens on `127.0.0.1` only. Requests from other web
  pages open in your browser are rejected (Origin / `Sec-Fetch-Site` checks), and the
  `Host` header must be `localhost` or an IP address (blocks DNS-rebinding attacks).
- **Phone access is opt-in.** Turning on *LAN access* in the device window lets the server
  listen on your network. Every other device must pair with a secret token (QR code or
  link); the token can be regenerated at any time. Actions that touch the computer itself
  (Save As dialogs, updates, installs, deleting models, restart) only work on the computer.
- **Verified downloads.** Everything G-Toolbox downloads uses verified HTTPS. Model weights
  and the portable Python are checked against pinned SHA-256 hashes before use; the
  Microsoft VC++ installer must carry a valid Microsoft signature.
- **Signed updates.** The in-app updater installs only GitHub releases whose `SHA256SUMS`
  is signed with the project's ed25519 key ([public key](release-signing-key.pub.pem)).
- G-Toolbox does not change Windows security settings (no Defender exclusions).

Found a security problem? Please report it privately to the author instead of opening a
public issue.

---

## 📦 Install

Download from [**GitHub Releases**](https://github.com/Gorkem-Taha/G-Toolbox/releases/latest).
Every release lists the SHA-256 of each file in `SHA256SUMS` (see
[Verifying downloads](#-verifying-downloads)).

### 🪟 Windows 10 / 11 — `G-Toolbox-v<version>-Windows.zip`

1. Extract the zip to a folder you can write to (e.g. `Documents\G-Toolbox`).
2. Run **`G-Toolbox.exe`**. The launcher is not code-signed, so SmartScreen may ask for
   confirmation (*More info → Run anyway*).
3. On first start the setup window downloads a portable Python 3.10 (hash-verified) and
   installs the exact dependency versions from `requirements-desktop.lock`. Tick *Install AI
   engine* to set up the AI tools at the same time, or do it later from the app.
4. A Start-menu shortcut is created, so you can find G-Toolbox from Windows Search.

Everything (Python runtime, settings, temporary files, models) stays inside that folder.
To uninstall, delete the folder and the *G-Toolbox* Start-menu shortcut
(the launcher also registers `HKCU\Software\Microsoft\Windows\CurrentVersion\App Paths\G-Toolbox.exe`).

### 🐧 Linux — `G-Toolbox-x86_64.AppImage`

Self-contained: includes Python 3.11, the core dependencies and FFmpeg.

```bash
chmod +x G-Toolbox-x86_64.AppImage
./G-Toolbox-x86_64.AppImage
```

The app opens in your browser. Settings, temporary files, models and AI libraries live in
`~/.local/share/g-toolbox`. The AppImage uses the static type2 runtime (no `libfuse2`
needed); on systems without FUSE at all (some containers), run it with
`--appimage-extract-and-run`.

### 📱 Android — `G-Toolbox.apk`

The Android app is a remote for G-Toolbox running on your computer (the heavy work runs on
the computer):

1. On the computer: open G-Toolbox → device mode button (top right) → **Enable LAN access**,
   then restart G-Toolbox.
2. Install the APK on the phone (allow *Install unknown apps* for your browser or file
   manager when asked).
3. Open the app and **scan the QR code** shown in G-Toolbox's device window (or paste the
   pairing link). Phone and computer must be on the same Wi-Fi.

You can also open the pairing link in any phone browser instead of installing the app.

### 💻 From source

```bash
git clone https://github.com/Gorkem-Taha/G-Toolbox.git
cd G-Toolbox
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install --require-hashes -r requirements-desktop.lock
python desktop_app.py          # native window (pywebview)
# or: python main.py           # browser mode; add --lan for phone access
```

FFmpeg must be on `PATH` for the media tools. AI engines: `pip install -r requirements-ai.txt`
or use the in-app AI setup.

---

## 🧠 AI engines and hardware

The in-app **AI setup** installs PyTorch and the AI libraries, then downloads and verifies
the model weights (~460 MB in total). *Delete AI models* in the same menu frees the space
again, and *Purge VRAM* unloads models from memory.

| Engine | Model size | Without a GPU |
| :--- | :--- | :--- |
| Real-ESRGAN (upscaler) | 67 MB + 18 MB | Works, slow on large images |
| LaMa (magic eraser) | ~200 MB | Works |
| U²-Net (background remover) | ~176 MB | Works well |
| faster-whisper (transcriber) | 75 MB (tiny) – ~3 GB (large-v3), downloaded per model size | Works (INT8) |
| Demucs (stems) | downloaded on first use | Works, a few minutes per song |

**GPU acceleration:** the AI setup installs the **CPU** build of PyTorch, which works on
every machine. If you have an NVIDIA GPU, replace it with a CUDA build to speed up the
upscaler, eraser, transcriber and separator considerably — for example on Windows, from the
G-Toolbox folder:

```powershell
runtime\python.exe -m pip install --force-reinstall torch torchvision --index-url https://download.pytorch.org/whl/cu124
```

GTX 16xx and older cards automatically use FP32 for the upscaler (their FP16 output is broken).
Recommended: 8 GB RAM (16 GB for Demucs), 10 GB free disk space.

---

## ✅ Verifying downloads

```bash
# 1. The manifest is signed by the G-Toolbox release key (OpenSSL 3)
openssl pkeyutl -verify -pubin -inkey release-signing-key.pub.pem -rawin \
        -in SHA256SUMS -sigfile SHA256SUMS.sig
# 2. Your files match the manifest
sha256sum --ignore-missing -c SHA256SUMS
```

---

## 🛠️ Development

### Layout

```
main.py              entry point: python main.py [--lan] [--port N] [--no-browser] / uvicorn main:app
desktop_app.py       native window (pywebview), falls back to the browser
gtoolbox/
  config.py          paths (GTOOLBOX_DATA_DIR), settings, constants
  security.py        loopback/LAN policy, pairing token, request guard
  net.py             verified HTTPS, hashing, Authenticode
  ai.py              model registry (pinned hashes), AI runtime, setup, caches
  media.py           FFmpeg / Pillow helpers
  files.py           uploads, temp-file cleanup, progress
  dialogs.py         native Save As
  updates.py         signed updates
  downloads.py       yt-dlp tasks
  app.py             FastAPI app (middleware, errors, static files, routers)
  routers/           system, media, ai, video, documents, updates
templates/, static/  web UI (vanilla JS; vendored Tailwind CSS, Font Awesome, fonts)
launcher/            Windows launcher (C#, .NET Framework 4.8)
android/             Android client (Java, WebView)
scripts/             AppImage / Windows bundle builds, release signing, lock files
tests/               pytest suite (security, supply chain, media, offline, version)
```

Mutable state shared between modules (loaded AI libraries, model caches, the pairing token)
is owned by one module and must be read as `ai.torch`, `security.ACCESS_TOKEN`, … — never
copied with `from module import name`.

### Common tasks

```bash
pip install --require-hashes -r requirements-dev.lock && pytest   # tests (needs ffmpeg)
python -m pyflakes gtoolbox main.py desktop_app.py tests          # lint
npm install && npm run build      # rebuild Tailwind CSS after adding classes; re-vendor assets
scripts/lock_requirements.sh      # refresh the *.lock files after editing requirements-*.txt (needs uv)
scripts/build_appimage.sh         # → dist/G-Toolbox-x86_64.AppImage
python scripts/build_windows_bundle.py   # → dist/G-Toolbox-v<version>-Windows.zip (needs the .NET SDK)
(cd android && ./gradlew assembleDebug)  # → APK (JDK 17 + Android SDK 34)
```

The version is defined once, in `gtoolbox/__init__.py`.

### Releasing

1. Bump `__version__` in `gtoolbox/__init__.py`, commit, then `git tag v<version> && git push --tags`.
2. The **Release** workflow tests and builds everything and creates a **draft** release
   with `SHA256SUMS`.
3. If the `RELEASE_SIGNING_KEY` secret is not configured, sign locally and upload the
   signature: `python scripts/sign_release.py <folder-with-the-release-files>` →
   `SHA256SUMS.sig`. Releases without a valid signature are ignored by the in-app updater.
4. Optional secrets for a release-signed APK: `ANDROID_KEYSTORE_BASE64`,
   `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, `ANDROID_KEY_PASSWORD`.

---

## 📜 License

[CC BY-NC 4.0](LICENSE) © [Görkem Taha](https://github.com/Gorkem-Taha). Third-party
components, the bundled FFmpeg (GPL) and model licenses are listed in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Downloading videos may be restricted by a
site's terms of service; you are responsible for how you use the downloader.
