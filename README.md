# ⚡ G-Toolbox | Premium AI-Powered Local Toolkit & Mobile Studio

![Version](https://img.shields.io/badge/version-4.3.0-blue.svg)
[![Release](https://img.shields.io/github/v/release/Gorkem-Taha/G-Toolbox?color=success)](https://github.com/Gorkem-Taha/G-Toolbox/releases/latest)
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

## 📦 İndirme ve Kurulum Rehberi (Installation & Quick Start Guide)

G-Toolbox, masaüstü (Windows, Linux) ve mobil (Android) platformlarda sıfır bulut bağımlılığıyla çalışacak şekilde paketlenmiştir. İhtiyacınıza uygun kurulum yöntemini seçin:

### 📥 Resmi Dağıtım Paketleri (v4.3.0 Releases)

Tüm resmi ikili dosyaları doğrudan [**GitHub Releases (v4.3.0)**](https://github.com/Gorkem-Taha/G-Toolbox/releases/tag/v4.3.0) sayfasından veya yerel depodaki `Releases/` klasöründen edinebilirsiniz:

| Platform / Paket | Dosya Adı | Boyut | Açıklama & Mimari |
| :--- | :--- | :--- | :--- |
| **🪟 Windows (Tam Paket)** | [**`G-Toolbox-v4.3.0-Windows.zip`**](https://github.com/Gorkem-Taha/G-Toolbox/releases/download/v4.3.0/G-Toolbox-v4.3.0-Windows.zip) | ~77 MB | Python sanal ortam otomasyonu (`installation.bat`) ve yerel C# başlatıcı içerir. |
| **🪟 Windows (Başlatıcı)** | [**`G-Toolbox.exe`**](https://github.com/Gorkem-Taha/G-Toolbox/releases/download/v4.3.0/G-Toolbox.exe) | ~19 KB | Hızlı splash screen (<30ms), Windows Arama ve Görev Çubuğu entegrasyonu. |
| **🐧 Linux (Taşınabilir)** | [**`G-Toolbox-x86_64.AppImage`**](https://github.com/Gorkem-Taha/G-Toolbox/releases/download/v4.3.0/G-Toolbox-x86_64.AppImage) | ~1.15 MB | Kurulum gerektirmeyen tekil çalıştırılabilir Linux paketi (Ubuntu, Debian, Fedora, Arch). |
| **📱 Android (Mobil)** | [**`G-Toolbox.apk`**](https://github.com/Gorkem-Taha/G-Toolbox/releases/download/v4.3.0/G-Toolbox.apk) | ~5.27 MB | Çift modlu (PC GPU Akışı + Çevrimdışı Bağımsız) yerel Android uygulaması. |

---

### 🐧 Linux (AppImage) Detaylı Kurulum ve Çalıştırma Rehberi

Linux kullanıcıları için G-Toolbox, tek bir bağımsız dosya olan `AppImage` formatında paketlenmiştir. Sistem kütüphanelerinizi kirletmeden tüm modern Linux dağıtımlarında çalışır.

#### 1. İndirme ve Çalıştırma Yetkisi Verme
Dosyayı doğrudan [GitHub Releases](https://github.com/Gorkem-Taha/G-Toolbox/releases/download/v4.3.0/G-Toolbox-x86_64.AppImage) üzerinden veya yerel `Releases/` dizininden temin edip terminalde çalıştırma izni verin:
```bash
# GitHub Releases üzerinden doğrudan indirmek için:
wget https://github.com/Gorkem-Taha/G-Toolbox/releases/download/v4.3.0/G-Toolbox-x86_64.AppImage

# Çalıştırma yetkisi verin
chmod +x G-Toolbox-x86_64.AppImage
```

#### 2. Uygulamayı Başlatma
```bash
./G-Toolbox-x86_64.AppImage
```

#### 3. FUSE (Filesystem in Userspace) Çözümü (Ubuntu 22.04+, Debian 12, Fedora 36+)
Modern Linux dağıtımlarında (özellikle Ubuntu 22.04 LTS ve sonrası) `libfuse2` varsayılan kurulu gelmeyebilir. Eğer `./G-Toolbox-x86_64.AppImage` komutunu verdiğinizde:
`dlopen(): error loading libfuse.so.2` veya `AppImages require FUSE to run` hatasıyla karşılaşırsanız aşağıdaki adımlardan birini uygulayın:

* **Yöntem A (Önerilen - FUSE Kütüphanesini Kurma):**
  - **Ubuntu / Debian / Linux Mint / Pop!_OS:**
    ```bash
    sudo apt update && sudo apt install -y libfuse2
    ```
  - **Fedora / RHEL / CentOS:**
    ```bash
    sudo dnf install fuse-libs
    ```
  - **Arch Linux / Manjaro:**
    ```bash
    sudo pacman -S fuse2
    ```

* **Yöntem B (Kütüphane Kurmadan Doğrudan Çalıştırma):**
  Sisteminize root yetkisiyle paket kurmak istemiyorsanız, dahili ayıklama parametresiyle doğrudan çalıştırabilirsiniz:
  ```bash
  ./G-Toolbox-x86_64.AppImage --appimage-extract-and-run
  ```

#### 4. Masaüstü & Uygulama Menüsü Entegrasyonu (XDG Menü)
G-Toolbox'ı GNOME, KDE Plasma veya XFCE uygulama menüsüne eklemek için:
```bash
# Çalıştırılabilir dosyayı kullanıcı ikili dizinine taşıyın
mkdir -p ~/.local/bin ~/.local/share/applications
cp G-Toolbox-x86_64.AppImage ~/.local/bin/g-toolbox
chmod +x ~/.local/bin/g-toolbox

# Masaüstü kısayol dosyasını kopyalayın
cp g-toolbox.desktop ~/.local/share/applications/
```

#### 5. Kaynak Koddan Kendi AppImage Paketinizi Derleme
Dahili `build_appimage.sh` otomasyon betiği ile yerel sisteminizde sıfırdan AppImage üretebilirsiniz:
```bash
chmod +x scripts/build_appimage.sh
./scripts/build_appimage.sh
```

---

### 📱 Android (.apk) Detaylı Kurulum ve Kullanım Rehberi

G-Toolbox Android sürümü, hem telefonunuzu güçlü masaüstü AI sunucunuza bağlayan bir uzaktan kumanda hem de tek başına çalışan bağımsız bir çevrimdışı medya atölyesidir.

#### 1. APK Dosyasını Yükleme
1. [**`G-Toolbox.apk`**](https://github.com/Gorkem-Taha/G-Toolbox/releases/download/v4.3.0/G-Toolbox.apk) dosyasını doğrudan telefonunuzun tarayıcısıyla indirin veya bilgisayarınızdan USB kablosu, Bluetooth ya da yerel ağ ile telefonunuza aktarın.
2. İndirilen `G-Toolbox.apk` dosyasına dokunun.
3. Android güvenlik uyarısı verirse:
   - **"Ayarlar" -> "Bilinmeyen uygulamaları yükle" (Install Unknown Apps)** bölümüne gidin.
   - Dosyayı açtığınız tarayıcıya (ör. Chrome) veya Dosya Yöneticisine **"Bu kaynaktan izin ver"** anahtarını açın.
4. **"Yükle"** butonuna dokunarak kurulumu tamamlayın.
5. Uygulamayı ilk kez açtığınızda galeri ve medya erişimi için istenen izinleri onaylayın.

#### 2. Çift Çalışma Modu (Dual-Mode Architecture)

Uygulama açılışında karşınıza çıkan **Akıllı Çalışma Modu** seçenekleri:

```
                  ┌────────────────────────────────────────────────┐
                  │          G-Toolbox Operating Modes             │
                  └───────────────────────┬────────────────────────┘
                                          │
                  ┌───────────────────────┴────────────────────────┐
                  ▼                                                ▼
     [Mod 1: PC Sunucu / GPU Akışı]                   [Mod 2: Yerel / Bağımsız Mod]
   • Telefon yerel Wi-Fi üzerinden PC'ye bağlanır   • Tamamen çevrimdışı ve bağımsız
   • PC'deki RTX/GTX GPU gücünü kullanır            • Telefonun kendi donanımını (WASM/Canvas) kullanır
   • 4x AI Upscale, Inpainting & 4K video indirme   • Hızlı görsel dönüştürme ve EXIF temizleme
   • Telefonda sıfır ısınma ve sıfır pil tüketimi   • PC kapalıyken bile kesintisiz çalışır
```

##### ⚡ Mod 1: PC Sunucu & GPU Hızlandırmalı Mod (Önerilen)
Masaüstü bilgisayarınızdaki güçlü NVIDIA GPU donanımını telefonunuzdan kullanın:
1. Bilgisayarınızda G-Toolbox'ı başlatın (`G-Toolbox.exe` veya `python main.py`). Uygulama yerel ağda dinlemeye başlar.
2. Telefonunuzun bilgisayarınızla **aynı Wi-Fi ağına** bağlı olduğundan emin olun.
3. Bilgisayar ekranında veya terminalde görüntülenen yerel IP adresini not edin (örneğin: `http://192.168.1.35:8000`).
4. Android uygulamasında **"PC Server Mode"** seçin ve bilgisayarınızın IP adresini girerek **"Bağlan"** butonuna dokunun.
5. Telefonunuzdan seçtiğiniz fotoğraflar arka planda PC'nizin ekran kartına gönderilir; Real-ESRGAN süper çözünürlük veya LaMa nesne silme motorunda işlenip sonuç doğrudan telefonunuza indirilir. Telefonunuz asla ısınmaz ve bataryanız korunur.

##### 🔋 Mod 2: Yerel / Bağımsız Mod (Standalone On-Device)
Bilgisayarınız kapalıyken veya seyahatteyken:
1. Uygulamada **"Local Mode"** seçeneğine dokunun.
2. Telefonun yerel işlemcisi ve HTML5 Canvas/WebAssembly motoru devreye girer.
3. Görsel formatı dönüştürme (PNG, JPEG, WebP), görsel boyutlandırma ve güvenlik odaklı EXIF meta veri temizleme işlemlerini hiçbir sunucuya veya internete ihtiyaç duymadan tamamen cihazınızda gerçekleştirin.

---

### 🪟 Windows Detaylı Kurulum ve Çalıştırma Rehberi

#### 1. Hızlı Kurulum Adımları
1. [**`G-Toolbox-v4.3.0-Windows.zip`**](https://github.com/Gorkem-Taha/G-Toolbox/releases/download/v4.3.0/G-Toolbox-v4.3.0-Windows.zip) paketini indirin ve bir klasöre çıkartın.
2. Klasör içerisindeki **`installation.bat`** dosyasını çalıştırın. Bu script:
   - Python 3.10+ varlığını denetler.
   - İzole bir `.venv` sanal ortamı kurar.
   - Gerekli tüm yapay zeka (`torch`, `torchvision`, `basicsr`, `rembg`, `fastapi` vb.) bağımlılıklarını eksiksiz yükler.
3. Kurulum bittikten sonra **`G-Toolbox.exe`** dosyasına çift tıklayarak uygulamayı başlatın.

#### 2. Native Desktop Başlatıcı Özellikleri
* **Anında Splash Screen (<30ms):** Arka planda FastAPI servisi ve yapay zeka modelleri hazırlanırken anında şık, koyu temalı bir yükleme ekranı gösterilir.
* **Windows Arama Entegrasyonu:** İlk çalıştırmada sistem otomatik olarak Başlat menüsü kısayolunu (`%APPDATA%\Microsoft\Windows\Start Menu\Programs\G-Toolbox.lnk`) ve kayıt defteri yollarını oluşturur. Başlat'ı açıp `G-Toolbox` yazdığınızda doğrudan bulunup açılır.
* **Resmi İkon ve Görev Çubuğu:** Win32 API (`SetCurrentProcessExplicitAppUserModelID`) entegrasyonu sayesinde görev çubuğunda ve pencerede resmi G-Toolbox logosu görünür.
* **Tek Tıkla Model Temizleme:** Arayüz üst menüsünden tek tıkla ~460 MB'lık yapay zeka modellerini temizleyip disk alanı açabilirsiniz (`/api/delete-ai-models`).

---

### 💻 Geliştiriciler İçin Kaynak Koddan Manuel Kurulum (Developer Setup)

Projeyi doğrudan kaynak kod üzerinden çalıştırmak ve geliştirmek için:

```bash
# 1. Depoyu klonlayın
git clone https://github.com/Gorkem-Taha/G-Toolbox.git
cd G-Toolbox

# 2. Python sanal ortamı oluşturun ve aktif edin
python -m venv venv

# Windows üzerinde:
.\venv\Scripts\activate

# Linux / macOS üzerinde:
source venv/bin/activate

# 3. Paketleri yükleyin
pip install --upgrade pip
pip install -r requirements.txt

# 4. Sunucuyu başlatın
python main.py
```
Sunucu başladığında varsayılan tarayıcınızda otomatik olarak `http://localhost:8000` sayfası açılacaktır.

---

## 🛠️ Comprehensive Technology Stack & Architecture (Kullanılan Teknolojiler)

G-Toolbox combines modern asynchronous web architecture, cutting-edge local computer vision models, neural audio processing pipelines, and native cross-platform binaries to deliver a zero-cloud, privacy-first workstation.

### 📊 Technology Stack Overview

| Domain / Layer | Primary Technology | Version / Specification | Architectural Role & Implementation Details |
| :--- | :--- | :--- | :--- |
| **Core Runtime & Language** | **Python** | `3.10+` | Core execution environment, asynchronous task orchestrator, native subprocess controller. |
| **Backend & Web Framework** | **FastAPI** | `0.100+` | High-throughput asynchronous REST API, streaming response handlers, SSE / progress routing. |
| **ASGI Web Server** | **Uvicorn** | `Standard` | Asynchronous Server Gateway Interface for high-concurrency LAN streaming and local HTTP serving. |
| **Data Validation & Schemas** | **Pydantic** | `v2.x` | Runtime data validation, request body modeling, type coercion, and strict error serialization. |
| **Templating Engine** | **Jinja2** | `3.1+` | Server-side template rendering for dynamic HTML views, internationalization tokens, and modals. |
| **Form & Media Ingestion** | **python-multipart** | Latest | High-performance streaming multipart/form-data processor for large media and video uploads. |
| **Deep Learning Engine** | **PyTorch & Torchvision** | `2.1+ (CUDA 12.1 / CPU)` | Tensor computation, dynamic neural graph execution, automatic mixed-precision (FP16/FP32). |
| **AI Super Resolution** | **Real-ESRGAN** | `RRDBNet` (23 & 6 Block) | `RealESRGAN_x4plus` (67 MB) & `anime_6B` (18 MB) models, Lanczos RGBA transparency handling. |
| **Computer Vision Toolbox** | **BasicSR** | `1.4+` | Specialized deep-learning image and video restoration framework powering the ESRGAN pipeline. |
| **Generative Inpainting** | **LaMa (Large Mask)** | `simple-lama-inpainting` | Fast Fourier Convolution (`big-lama` FFC-ResNet) for zero-shot object removal & background repair. |
| **Salient Object Detection** | **rembg (U^2-Net)** | `ONNX Runtime` | Two-level nested U-structure network for fine-grained alpha matting and background removal. |
| **Speech-to-Text & Subtitles** | **faster-whisper** | `CTranslate2` | 4x faster Whisper inference with INT8 (CPU) and FP16 (GPU) quantization across 90+ languages. |
| **Vocal & Music Separation** | **Meta Demucs v4** | `htdemucs` (Hybrid Transformer)| High-fidelity 2-stem (Vocals/Music) and 4-stem (Vocals, Drums, Bass, Other) track separation. |
| **Computer Vision Matrix Ops** | **OpenCV (`opencv-python`)**| `4.8+` | Pixel matrix manipulations, Unicode path buffer conversion (`np.fromfile`, `cv2.imencode`). |
| **Digital Imaging & Metadata** | **Pillow (PIL)** | `10.0+` | Multi-format image encoding/decoding, Lanczos interpolation, EXIF/IPTC/XMP forensic scrubbing. |
| **Numerical Computing** | **NumPy** | `1.24+` | Vectorized multidimensional array processing, color space transforms, and raw byte buffers. |
| **Multimedia DSP & Transcoding**| **FFmpeg & ffmpeg-python** | `v6.0+ (Bundled)` | Transcoding, hardsub subtitle burner, 2-pass palettegen GIF/WebP animator, FFT noise cleaning. |
| **Streaming Media Extraction** | **yt-dlp** | Auto-Updating Core | Multi-client header rotation (`ios`, `android`, `mweb`) bypassing YouTube HTTP 403 throttling. |
| **Military-Grade Encryption** | **pyAesCrypt** | `AES-256-CBC` | Secure PBKDF2 HMAC-SHA256 key derivation with chunked streaming buffer (`64 KB`) encryption. |
| **Document Processing** | **pypdf** | `3.15+` | Pure-Python PDF parsing, lossless page-range splitting, document merging, and text extraction. |
| **Desktop GUI Container** | **pywebview** | `4.3+` | Native desktop window embedding Microsoft Edge WebView2 (Windows) and WebKitGTK (Linux). |
| **Native Windows Launcher** | **C# / .NET (WinForms)** | `C# 7.0+ / Win32` | Instant (<30ms) splash screen, `SetCurrentProcessExplicitAppUserModelID`, native icon binding. |
| **Windows Packaging & Setup** | **Inno Setup 6** | `6.2+` | Production-grade scriptable Windows setup installer compiler (`installer.iss`) with uninstaller hooks. |
| **Linux Portable Packaging** | **AppImageKit** | `x86_64` | Portable single-file Linux bundle with XDG desktop specifications (`g-toolbox.desktop`). |
| **Frontend Styling & UI** | **HTML5 & Modern CSS3** | Custom VIP Dark Theme | Responsive glassmorphic interface, CSS Grid/Flexbox, custom micro-interactions, zero CSS bloat. |
| **Client-Side Scripting** | **Vanilla JavaScript** | `ES6+ (ES2022)` | Async/await fetch architecture, FileReader API, HTML5 Canvas offline graphics processing. |
| **Progressive Web App (PWA)** | **Service Worker & Manifest**| `W3C PWA Standard` | Offline asset caching (`sw.js`) and standalone home-screen installation on Android/iOS browsers. |
| **Mobile Native Wrapper** | **Android SDK & Java** | `API 26-34` | Android WebView wrapper (`MainActivity.java`) with hardware acceleration and file-picker hooks. |
| **Cloud CI/CD Workflows** | **GitHub Actions** | Ubuntu Runners | Automated cloud pipelines for headless AppImage compilation and Android `.apk` generation. |

---

### 🔬 Deep Architectural Breakdown by Subsystem

#### 1. 🧠 Artificial Intelligence & Deep Learning Engines
* **Real-ESRGAN (`RRDBNet`):**
  * Employs Residual-in-Residual Dense Block (`RRDB`) networks trained with adversarial loss for photorealistic super-resolution.
  * **Dual Engine Integration:** Offers `RealESRGAN_x4plus` (23 blocks, deep feature extraction for photographs) and `RealESRGAN_x4plus_anime_6B` (6 blocks, lightweight and artifact-free for digital art).
  * **Alpha Channel Preservation:** Transparent PNG images are automatically bifurcated; RGB channels undergo neural upscaling while the alpha transparency mask is resized via high-order Lanczos interpolation before alpha recombination.
  * **Hardware Fallback Guard:** Automatically audits GPU architecture; older Pascal and GTX 16xx (Turing) chips automatically fallback to FP32 calculation to circumvent hardware-level `NaN` blank pixel bugs.
  * **In-Memory Singleton:** Models persist in memory (`_UPSCALER_INSTANCES`) across requests, slashing inference latency from ~4.5s to ~1.2s on subsequent runs.
* **LaMa Inpainting (`SimpleLama`):**
  * Based on Large Mask Inpainting with Fast Fourier Convolutions (`FFC-ResNet`).
  * Features an image-wide receptive field capable of understanding structural context, enabling seamless text, watermark, and object removal without seam artifacts.
  * Persisted via a global model cache (`_LAMA_INSTANCE`) for instantaneous reactive painting.
* **rembg & ONNX Runtime (U^2-Net):**
  * Implements a ReSidual U-block (`RSU`) architecture that captures multi-scale contextual features without increasing feature map memory footprints.
  * Executed via ONNX Runtime with automatic hardware acceleration provider selection (CUDA, DirectML, or optimized CPU threads).
* **Faster-Whisper (Speech Recognition):**
  * Powered by `CTranslate2`, an optimized inference engine for Transformer models implementing weights quantization (INT8 on CPU, FP16 on GPU).
  * Outperforms standard OpenAI Whisper implementations by up to 4x in inference speed while consuming 50% less memory.
  * Emits structured JSON segments, SRT, VTT, and plain text transcripts with millisecond-accurate timestamps.
* **Meta Demucs v4 (`htdemucs`):**
  * State-of-the-art hybrid transformer architecture combining time-domain convnets with frequency-domain cross-attention.
  * Features in-process native execution with fallback subprocess routing, enabling vocal isolation and 4-stem studio separation.

#### 2. 🎬 Media Engineering, Audio DSP & Extraction
* **FFmpeg Pipeline Architecture:**
  * **Hardsub Engine:** Utilizes the FFmpeg `subtitles` filter graph to bake stylized SRT and VTT captions directly into video streams with custom font rendering.
  * **Two-Pass GIF / WebP Generation:** Automatically passes media through `palettegen` to generate an adaptive 256-color palette, followed by `paletteuse` with custom dither algorithms, yielding ultra-crisp animations at minimal file sizes.
  * **Spectral Noise Suppressor:** Executes Adaptive Fast Fourier Transform filtering (`afftdn`) coupled with voice-frequency bandpass equalization (`highpass=f=200, lowpass=f=3500`) to eliminate microphone hiss, air conditioning hum, and fan noise.
  * **Audio Spatializer (Slowed+Reverb & Nightcore):** Implements complex `aecho` reflection matrices and `rubberband`/`atempo` algorithms for lossless pitch and tempo modulation.
* **yt-dlp Extraction Architecture:**
  * Employs multi-client identity rotation (`android`, `ios`, `mweb`, `web`) with spoofed headers to bypass modern YouTube HTTP 403 Forbidden client-verification mechanisms.
  * Features a dedicated `/update-ytdlp` endpoint to hot-patch the extraction engine in production without requiring full software reinstallation.

#### 3. 🔒 Security, Cryptography & Forensics
* **The File Vault (pyAesCrypt):**
  * Implements `AES-256-CBC` encryption with HMAC-SHA256 authentication.
  * Key derivation is hardened via PBKDF2 with dynamic cryptographic salts.
  * Operates on a chunked 64 KB memory buffer, enabling secure encryption and decryption of multi-gigabyte archives without RAM exhaustion.
* **Zero-Trace EXIF & Metadata Scrubbing:**
  * Inspects GPS latitude/longitude, camera serial numbers, lens specifications, and editing software stamps using `PIL.ExifTags`.
  * Scrubbing creates a sanitized raw pixel buffer and reconstructs the image from scratch, stripping EXIF, IPTC, and XMP metadata entirely.

#### 4. 🖥️ Desktop, OS Integration & Mobile Dual-Mode
* **Win32 & .NET Native Launcher (`launcher.cs`):**
  * Written in C# with Win32 P/Invoke declarations (`SetCurrentProcessExplicitAppUserModelID`, `WM_SETICON`).
  * Displays a dark splash screen in under 30ms, eliminating the traditional Python startup lag while launching the background FastAPI service.
* **pywebview Desktop Shell:**
  * Embeds modern Chromium (Edge WebView2) on Windows and WebKit on Linux.
  * Provides native window decorations, maximized startup, F11 borderless fullscreen toggle, and native file dialogs.
* **Mobile Dual-Mode System:**
  * **Mode 1 (Remote GPU Streaming):** Discovers the host's LAN IP via `/api/network-info` and establishes a CORS-enabled connection, streaming heavy GPU workloads to mobile browsers.
  * **Mode 2 (Local On-Device):** Executes offline client-side image resizing, format conversions, and metadata stripping using HTML5 Canvas and JavaScript FileReader directly in the mobile browser or native Android APK.

---

## 📜 License
This project is licensed under the [CC BY-NC 4.0 License](LICENSE).  
Developed with ❤️ by **[Görkem Taha](https://github.com/Gorkem-Taha)**
