# 📦 G-Toolbox v4.4.0 Release Binaries

This directory contains standalone portable Windows Launcher, Linux AppImage, and Android APK distribution packages for G-Toolbox.

---

## 📁 Package Manifest & SHA-256 Checksums

| File Name | Target Platform | Size | Architecture / Format | SHA-256 Checksum |
| :--- | :--- | :--- | :--- | :--- |
| **`G-Toolbox-v4.4.0-Windows.zip`** | Windows 10 / 11 (x64) | ~1.01 MB | Standalone Portable Source & Launcher Bundle | `2F3CD99FCC3E6080F81D8CD58BE4A70057A6F6F391F119B3E30E94CA26228206` |
| **`G-Toolbox.exe`** | Windows 10 / 11 (x64) | ~31.2 KB | Win32 / .NET Smart Portable Launcher | `3421A2384134DD1BA152A92F9E976D05E21A199167AAFFE2E9D879E4846603D9` |
| **`G-Toolbox-x86_64.AppImage`** | Linux (Ubuntu, Debian, Fedora, Arch) | ~1.15 MB | `x86_64` Standalone Portable | `0F7BE770D1B8B5C988CD2ACCF49F6081CE169B4B43D9D23B7C015FA1BEBD3F91` |
| **`G-Toolbox.apk`** | Android (Mobile & Tablet) | ~5.27 MB | `arm64-v8a / armeabi-v7a / x86_64` | `8F897B090C4D7B81FFF1B2CBB508DDD74A5DCCE84BFCC4A0ABB4519725DEEF8F` |

---

## 🪟 Windows (Portable Launcher) Quick Execution
1. Double-click **`G-Toolbox.exe`**.
2. If Python is missing or incompatible (e.g. Python 3.12+ build tool conflicts), the built-in Setup Engine automatically downloads an isolated Python 3.10.11 runtime (~8.2 MB), configures dependencies, and starts the desktop app.
3. AI weights and GPU engines can be installed on-demand inside the app via the AI Setup Wizard.

---

## 🐧 Linux (AppImage) Quick Execution
```bash
chmod +x G-Toolbox-x86_64.AppImage
./G-Toolbox-x86_64.AppImage
```
*If you encounter a FUSE error on modern Linux distributions (Ubuntu 22.04+, Debian 12, Fedora 36+):*
```bash
sudo apt install -y libfuse2
# or run directly without installing FUSE:
./G-Toolbox-x86_64.AppImage --appimage-extract-and-run
```

---

## 📱 Android (APK) Installation
1. Download or transfer `G-Toolbox.apk` to your Android device via USB/Bluetooth.
2. Open the file and grant *"Install Unknown Apps"* permission if prompted by your browser or file manager.
3. Launch the app:
   - **PC Server Mode (GPU Acceleration):** Connect to the same local Wi-Fi as your PC, enter your computer's local IP address (`http://192.168.x.x:8000`), and stream 4x AI Upscaling and media downloads powered by your PC's RTX/GTX GPU.
   - **Local Mode (Offline):** Run client-side offline image conversion, resizing, and EXIF metadata stripping directly on your mobile device without any server.

---

> 🌐 **Official GitHub Release Page:** [https://github.com/Gorkem-Taha/G-Toolbox/releases/tag/v4.4.0](https://github.com/Gorkem-Taha/G-Toolbox/releases/tag/v4.4.0)
