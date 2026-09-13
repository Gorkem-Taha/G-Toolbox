# ⚡ G-Toolbox | Premium AI-Powered Local Toolkit & Mobile Studio

![Version](https://img.shields.io/badge/version-4.3.0-blue.svg)
![License](https://img.shields.io/badge/license-Non--Commercial-red.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20Android-lightgrey.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Build](https://img.shields.io/badge/build-Native%20Desktop%20%26%20AppImage%20%26%20APK-purple.svg)

G-Toolbox is a premium, all-in-one local workspace that combines state-of-the-art Artificial Intelligence (Computer Vision) models, military-grade encryption, universal media conversion, and cross-platform mobile connectivity into a single, sleek VIP interface. 

> ⚠️ **IMPORTANT LICENSE & COMMERCIAL USE WARNING**
> This software is strictly licensed for **Personal and Educational Use Only**. Using G-Toolbox (or its underlying code) for commercial purposes, within a corporate network, for client projects, or in any revenue-generating capacity is **STRICTLY PROHIBITED** without a valid Commercial License. For commercial licensing inquiries, please contact the developer.

---

## 🔒 The Ultimate Privacy: Your Data Stays Yours

In a world where every SaaS application uploads your private documents and photos to the cloud, **G-Toolbox operates 100% locally on your machine.**
* **Zero Cloud Uploads:** Your files never leave your computer or local network.
* **No API Keys Required:** We use open-source, local AI models. No hidden subscription fees or credit limits.
* **Complete Offline Capability:** Once installed, you can disconnect your internet and continue working with military-grade encryption and AI generation.

---

## 📸 Screenshots & UI

### 🏠 The Workspace (Home)
![G-Toolbox Homepage](./static/menu.png?v=2)
*The dark-themed, premium interface designed for maximum productivity.*

### 🎨 AI Studio & Tools
![AI Tools](./static/bc_remove.png?v=2)
*Real-time progress bars, dual-engine AI selection, and seamless hardware acceleration.*

---

## 🚀 Detailed Tool Descriptions & Capabilities

### 1. 🌌 AI Image Upscaler (Dual Engine Super Resolution)
Upscale low-resolution or blurry images up to 4x (4K/8K resolution) without detail loss, powered by **Real-ESRGAN**.
* **Realistic / Photo Engine (`RealESRGAN_x4plus`):** 67 MB, 23-block deep neural network for natural photography, textures, and landscapes.
* **Anime / Digital Illustration Engine (`RealESRGAN_x4plus_anime_6B`):** 17.9 MB, 6-block lightweight network. 4x faster inference with razor-sharp lines and zero digital artifacting.
* **Full RGBA Transparency Support:** Transparent PNGs have their alpha channel isolated and seamlessly recombined via Lanczos filtering.
* **Hardware Safe (FP16 Fallback):** Automatically detects GTX 16xx (Turing) and older Pascal GPUs to prevent black/NaN image output.
* **VRAM Singleton:** Models are cached in memory (`_UPSCALER_INSTANCES`) to prevent memory leaks.

### 2. 🪄 Magic Eraser (AI Inpainting)
Remove unwanted objects, watermarks, text, or people from any photo. Powered by the **LaMa** model, it intelligently analyzes surrounding pixels to recreate the background flawlessly.

### 3. ✂️ Deep Background Remover
Instantly cut out the main subject of any photo with sub-pixel edge detection, powered by **U^2-Net** (`rembg`). Full i18n support and zero cloud dependency.

### 4. 🔒 The File Vault (AES-256 Encryption)
Military-grade file and folder encryption. Select a single file or an entire folder—the backend will automatically compress and lock it into an encrypted `.enc` vault with PBKDF2 key derivation.

### 5. 📥 Universal Media Downloader & yt-dlp Auto-Updater
Download high-quality videos or extract lossless audio directly from the web to your local drive.
* Powered by **yt-dlp** and **FFmpeg** with real-time progress tracking.
* **Anti-403 Multi-Client Routing:** Uses rotating client identifiers (`android`, `ios`, `mweb`, `web`) to bypass YouTube 403 Forbidden throttling.
* **One-Click yt-dlp Updater (`/update-ytdlp`):** Upgrade the internal streaming downloader engine in seconds.

### 6. 🔄 Universal File Converter & Media Tools
Convert image, audio, and video formats locally using **FFmpeg** architecture without uploading sensitive files to third-party servers.

### 7. 🧹 Automated Disk Hygiene & VRAM Unloader
* **Disk Purge:** Automatically removes orphaned temporary files in `uploads/` and `downloads/` on startup and during scheduled intervals.
* **Smart VRAM Purger (`/api/purge-vram`):** One-click button in the UI header to flush cached AI models (LaMa, Real-ESRGAN, Whisper) and release dedicated GPU VRAM / CPU RAM.

### 8. 🎙️ AI Vocal & Stems Separator (Demucs / UVR Lite)
Split songs or recorded audio into clean studio stems powered by **Meta's Demucs**.
* **Dual Stem Mode:** Instantly separate into Vocals and Instrumental backings.
* **4-Stem Quad Mode:** Separate full tracks into Vocals, Drums, Bass, and Other instruments.
* **Package & Download:** Auto-bundles generated stems into a single high-fidelity `.zip` archive with real-time processing progress.

### 9. 📝 Local AI Transcriber & Subtitle Generator (Faster-Whisper)
Generate instant timestamps and text transcripts from video or audio files 100% locally with **faster-whisper**.
* **Hardware Acceleration:** Auto-selects GPU FP16 or CPU INT8 for ultra-fast transcription.
* **Multi-Format Export:** Download transcripts as `.srt` subtitles, `.txt` readable transcripts, or structured `.json` with segment-level timestamps.
* **Language Support:** Auto-detection across 90+ languages, with optimized presets for Turkish, English, German, and French.

### 10. 🛡️ EXIF & Privacy Metadata Stripper
Inspect and scrub sensitive metadata embedded in photos before sharing online.
* **Full EXIF Inspection:** View GPS coordinates, camera model, lens parameters, date taken, and software tags.
* **Zero-Trace Stripping:** Strips EXIF, IPTC, XMP, and device fingerprints at pixel buffer level while preserving original image resolution and quality.

### 11. 🎬 High-Performance GIF & WebP Animator
Convert video clips to lightweight, smooth animated GIFs or modern animated WebP files using **FFmpeg**.
* **Time Slice Precision:** Define exact start (`HH:MM:SS`) and end times (or duration).
* **Two-Pass PaletteGen:** Generates a custom 256-color palette for crisp, non-dithered GIFs.
* **Custom Framerate & Scaling:** Control FPS (10-30), target width (320px to 1080px), and WebP compression quality.

### 12. 💬 Video Subtitle Burner (Hardsub)
Permanently embed SRT or VTT subtitle tracks into video files with custom fonts, colors, and border styles via FFmpeg.

### 13. 📄 Swiss Army PDF Toolkit
Complete client-side and backend PDF suite powered by `pypdf`:
* **PDF Merge:** Combine multiple documents preserving original order.
* **PDF Split:** Extract specific pages or intervals (e.g. `1-3, 5, 8-10`) into an independent PDF.
* **PDF Text Extraction:** Extract digital text from all pages into structured `.txt`.

### 14. 🎚️ Audio Effects & Speed Engine (Slowed+Reverb & Nightcore)
* **Slowed + Reverb:** Creates atmospheric spatial audio with tempo reduction and decay reverb.
* **Nightcore:** High-energy pitch shifting and tempo acceleration.
* **Fine-Tuning:** Custom sliders for speed/tempo (0.5x - 2.0x), pitch (0.5x - 2.0x), and room reverb.

### 15. 🧹 Spectral & Adaptive Noise Suppressor (FFT De-Noise)
Removes static hiss, fan whir, air conditioner hum, and room noise from microphone recordings or video audio using Adaptive Fast Fourier Transform filtering (`afftdn`) and Voice Focus bandpass.

---

## 💻 System Hardware Requirements (Local AI Engines)

Because **G-Toolbox runs 100% locally with zero cloud dependencies**, your processing speed and performance depend directly on your computer's hardware. The application dynamically routes workloads to **NVIDIA CUDA (GPU)** when available, with full fallback to **CPU (OpenMP / INT8)**.

### 🧠 Local AI Models & Resource Footprint

| AI Engine / Tool | Underlying Architecture | Model Weight Size | Min. Mode (CPU Fallback) | Recommended Mode (NVIDIA GPU) |
| :--- | :--- | :--- | :--- | :--- |
| **🌌 AI Image Upscaler** | Real-ESRGAN (`RRDBNet` / `x4plus` & `anime_6B`) | 67 MB / 18 MB | 8 GB RAM (CPU FP32, ~15–45s / img) | 4 GB+ VRAM GDDR6 (~1–3s / img) |
| **🪄 Magic Eraser** | LaMa Inpainting (`big-lama` FFC-ResNet) | ~200 MB | 8 GB System RAM | 3 GB – 4 GB+ VRAM |
| **✂️ Deep Background Remover** | U^2-Net / ONNX Runtime (`rembg`) | ~176 MB | 4 GB System RAM (~3–5s) | 2 GB+ VRAM (CUDA/DirectML) (~0.8s) |
| **🎙️ AI Vocal & Stems Separator** | Meta Demucs v4 (`htdemucs` 4-stem / 2-stem) | ~300 MB | 12–16 GB RAM (Multi-core CPU, ~2–4 min) | 6 GB – 8 GB+ VRAM (CUDA, ~15–30s) |
| **📝 Local Transcriber & Subtitles**| Faster-Whisper (`CTranslate2` base/small/med) | 150 MB – 1.5 GB | 8 GB RAM (INT8 Quantized) | 2 GB – 4 GB+ VRAM (FP16 Engine) |
| **🔄 Media Converter & Video Tools** | FFmpeg Native Core + Libx264/Libx265 | Bundled | 4-Core CPU / 4 GB RAM | NVENC / Hardware Acceleration |

---

### 🟢 Minimum Hardware Requirements (CPU Mode)
> Suitable for general file conversions, AES-256 encryption, background removal, and lightweight image editing. Heavier AI tasks (Demucs stem separation, 4K upscaling) will run on CPU threads at reduced speed.

* **Operating System:** Windows 10 / 11 (64-bit) or Linux (Ubuntu 20.04+, Debian 11+, Fedora 36+, Arch)
* **Processor (CPU):** Intel Core i3 / i5 (8th Gen+) or AMD Ryzen 3 / 5 (minimum 4 Cores / 8 Threads)
* **System Memory (RAM):** 8 GB DDR4 (12 GB+ recommended if multitasking)
* **Graphics (GPU):** Integrated Graphics (Intel UHD / Iris Xe / AMD Radeon Vega) or basic dedicated GPU
* **Disk Storage:** 10 GB free space (SSD recommended for model weights & PyTorch cache)
* **Network:** Required once during initial setup to download local AI models; 100% offline thereafter.

### 🚀 Recommended / Maximum Performance (Dedicated GPU Acceleration)
> Unlocks instant sub-second AI inference, 4K/8K real-time upscaling, rapid batch audio transcription, and seamless Demucs stem separation.

* **Operating System:** Windows 10 / 11 (64-bit) or Modern Linux with NVIDIA Driver 535+
* **Processor (CPU):** Intel Core i7 / i9 (10th Gen+) or AMD Ryzen 7 / 9 (3000 / 5000 / 7000+ Series, 6–8+ physical cores)
* **System Memory (RAM):** 16 GB – 32 GB DDR4 / DDR5
* **Dedicated GPU (VRAM):** **NVIDIA GeForce RTX 2060, RTX 3060, RTX 4060 or higher** with **6 GB to 12 GB+ GDDR6 VRAM**
  * *CUDA 12.1+ and Tensor Core acceleration are automatically detected and utilized.*
  * *GTX 1650/1660 Turing & Pascal cards are automatically supported via built-in FP16/FP32 NaN fallback.*
* **Disk Storage:** 20 GB+ free space on an **NVMe M.2 SSD** (for high-throughput model deserialization and temporary 4K video I/O)

> 💡 **VRAM Management Tip:** G-Toolbox features an on-demand **Smart VRAM Purger** (`/api/purge-vram`) accessible directly from the UI header to flush cached AI weights and immediately release VRAM for other GPU tasks.

---

## 🖥️ Modern Desktop Experience (Windows & Linux)

### 🚀 Instant Splash Screen & Native Windows Integration
* **Zero Startup Anxiety:** Clicking `G-Toolbox.exe` instantly (<30ms) launches an ultra-lightweight, dark-themed **Splash Screen** indicating progress ("Yapay zekâ ve medya motorları başlatılıyor..."). Users never wonder whether the application registered their click.
* **Custom App & Taskbar Icon:** Completely eliminates generic Python icons. Both the executable file, the native title bar, and the Windows Taskbar display the official G-Toolbox icon via native Win32 `SetCurrentProcessExplicitAppUserModelID` and `WM_SETICON` integration.
* **Maximized & Fullscreen by Default:** Desktop windows launch maximized to fill your monitor seamlessly, with full **F11** keyboard shortcut support for borderless fullscreen.
* **One-Click Local AI Deletion & Storage Management:** Users can check local model weights (Real-ESRGAN, LaMa, U2-Net) and delete them directly from the UI header to immediately reclaim ~460 MB of disk space.
* **Native "Save As" Dialog:** Downloaded YouTube videos and processed AI outputs prompt Windows Explorer / OS file dialogs directly to save anywhere on your disk.

---

## 🐧 Linux AppImage (Single-Click Portable)

G-Toolbox provides first-class Linux support without manual dependency wrangling:

* **Portable Executable:** Run anywhere with zero installation:
  ```bash
  chmod +x G-Toolbox-x86_64.AppImage
  ./G-Toolbox-x86_64.AppImage
  ```
* **One-Click Build Script:** Build your own AppImage locally on any Linux distribution (Ubuntu, Debian, Fedora, Arch):
  ```bash
  chmod +x scripts/build_appimage.sh
  ./scripts/build_appimage.sh
  ```
* **Automated Cloud CI/CD:** GitHub Actions (`.github/workflows/build-appimage.yml`) automatically compiles and releases fresh `G-Toolbox-x86_64.AppImage` binaries on every commit and release.
* **XDG Desktop Integration:** Includes `g-toolbox.desktop` and high-res icon assets for GNOME, KDE, and XFCE application menus.

---

## 📱 Mobile Dual-Mode & Android APK

G-Toolbox features a universal **Dual-Mode System** for mobile phones and tablets:

```
                  ┌────────────────────────────────────────────────┐
                  │          G-Toolbox Operating Modes             │
                  └───────────────────────┬────────────────────────┘
                                          │
                  ┌───────────────────────┴────────────────────────┐
                  ▼                                                ▼
     [Mode 1: PC Server / Remote]                     [Mode 2: Local On-Device]
   • Phone connects over Wi-Fi/LAN                  • Completely offline / standalone
   • Uses PC's GTX/RTX GPU power                    • Client-side (HTML5 Canvas/WASM)
   • 4x AI Upscale & 4K video downloads             • Image format conversion & compression
   • Zero phone heating or battery drain            • Runs when PC is powered off
```

1. **PC Server Mode (GPU-Accelerated):**
   * Pair your Android device to your computer via Wi-Fi (`http://YOUR_PC_IP:8000`).
   * Heavy AI inference and video downloads run on your computer's GPU and stream the final result back to your phone.
   * Features automatic LAN IP detection (`/api/network-info`) and full CORS support.
2. **Local Device Mode (On-Device / Offline):**
   * Use your mobile processor directly in the browser or APK. Perfect for quick image conversions, compression, and privacy cleaning when away from your PC.
3. **Android APK Wrapper (`android/`):**
   * Native Android WebView wrapper with camera, media gallery permissions, and file chooser support.
   * **Automated Cloud Builds:** Automated GitHub Actions workflow (`.github/workflows/build-apk.yml`) builds fresh `.apk` packages on every commit.
4. **Interactive Setup Wizard:** On first launch, the mobile onboarding modal guides users through choosing their preferred operating mode with automatic PC detection.

---

## 📜 License
This project is licensed under the [CC BY-NC 4.0 License](LICENSE).  
Developed with ❤️ by **[Görkem Taha](https://github.com/Gorkem-Taha)**
