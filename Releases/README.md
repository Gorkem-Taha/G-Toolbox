# 📦 G-Toolbox v4.4.0 Release Binaries

This directory contains standalone portable Windows Launcher, Linux AppImage, and Android APK distribution packages for G-Toolbox.

---

## 📁 Package Manifest & SHA-256 Checksums

| File Name | Target Platform | Size | Architecture / Format | SHA-256 Checksum |
| :--- | :--- | :--- | :--- | :--- |
| **`G-Toolbox.exe`** | Windows 10 / 11 (x64) | ~30.5 KB | Win32 / .NET Smart Portable Launcher | `8998d15ab314037385102e9a62a051410c0644654ad59d2ae6c507034d1cefca` |
| **`G-Toolbox-x86_64.AppImage`** | Linux (Ubuntu, Debian, Fedora, Arch) | ~1.15 MB | `x86_64` Standalone Portable | `0f7be770d1b8b5c988cd2accf49f6081ce169b4b43d9d23b7c015fa1bebd3f91` |
| **`G-Toolbox.apk`** | Android (Mobile & Tablet) | ~5.27 MB | `arm64-v8a / armeabi-v7a / x86_64` | `8f897b090c4d7b81fff1b2cbb508ddd74a5dcce84bfcc4a0abb4519725deef8f` |

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

> 🌐 **Official GitHub Release Page:** [https://github.com/Gorkem-Taha/G-Toolbox/releases/tag/v4.3.0](https://github.com/Gorkem-Taha/G-Toolbox/releases/tag/v4.3.0)
