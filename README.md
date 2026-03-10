# ⚡ G-Toolbox | Premium AI-Powered Local Toolkit

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-Non--Commercial-red.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)

G-Toolbox is a premium, all-in-one local workspace that combines state-of-the-art Artificial Intelligence (Computer Vision) models, military-grade encryption, and universal file conversion tools into a single, sleek VIP interface. 

> ⚠️ **IMPORTANT LICENSE & COMMERCIAL USE WARNING**
> This software is strictly licensed for **Personal and Educational Use Only**. Using G-Toolbox (or its underlying code) for commercial purposes, within a corporate network, for client projects, or in any revenue-generating capacity is **STRICTLY PROHIBITED** without a valid Commercial License. For commercial licensing inquiries and subscription plans, please contact the developer.

---

## 🔒 The Ultimate Privacy: Your Data Stays Yours

In a world where every SaaS application uploads your private documents and photos to the cloud, **G-Toolbox operates 100% locally on your machine.** * **Zero Cloud Uploads:** Your files never leave your computer.
* **No API Keys Required:** We use open-source, local AI models. No hidden subscription fees or credit limits.
* **Complete Offline Capability:** Once installed, you can disconnect your internet and continue working with military-grade encryption and AI generation.

---

## 📸 Screenshots

### 🏠 The Workspace (Home)
![G-Toolbox Homepage](/static/menu.png)
*The dark-themed, premium interface designed for maximum productivity.*

### 🎨 AI Studio & Tools
![AI Tools](docs/images/ai-tools.png)
*Real-time progress bars and seamless AI integration.*

---
## 🚀 The Arsenal (Detailed Tool Descriptions)

### 1. 🌌 AI Image Upscaler (Super Resolution)
Upscale low-resolution or blurry images to stunning 4K quality without losing detail, powered by the **Real-ESRGAN** model.
> ⚠️ **Hardware Warning:** This tool is extremely resource-intensive. When running at 4x scale, it will heavily utilize your Graphics Card (GPU) or CPU. **It is completely normal to hear your computer's cooling fans spin up to maximum speed.** The system uses *Tiling Optimization* to prevent your PC from freezing during this process.

### 2. 🪄 Magic Eraser (AI Inpainting)
Remove unwanted objects, text, or people from any photo. Powered by the **LaMa** model, it intelligently analyzes surrounding pixels to recreate the background flawlessly.
> 💡 *Note:* Requires moderate RAM usage during processing.

### 3. ✂️ Deep Background Remover
Instantly cut out the main subject of any photo with perfect edge detection, powered by the **U^2-Net** model. Say goodbye to manual masking.

### 4. 🔒 The File Vault (AES-256 Encryption)
Military-grade file and folder encryption. Select a single file or an entire folder—the backend will automatically compress and lock it into a `.enc` vault.
> 🛑 **Security Warning:** There is NO backdoor. If you forget the password you set, your files cannot be recovered by anyone, not even supercomputers.

### 5. 📥 Universal Media Downloader
Download high-quality videos or extract audio directly from the web straight to your local drive. Powered by **yt-dlp** and **FFmpeg**, bypassing the need for sketchy, ad-filled online downloaders. Supports real-time progress tracking!

### 6. 🔄 Universal File Converter
Convert images and audio formats locally using **FFmpeg** architecture without uploading your sensitive files to online servers. Keep your workflow offline and private.

### 7. ☁️ OTA Auto-Updater (Sync)
Stay up-to-date effortlessly. Click the "Sync" button in the app, and G-Toolbox will securely fetch the latest features from GitHub and patch itself without touching your personal files or virtual environment.

---

## 💻 System Requirements

Because G-Toolbox runs actual AI models locally, your hardware dictates the processing speed.

### 🟢 Minimum Requirements (Runs on CPU - Slower Processing)
* **OS:** Windows 10 (64-bit)
* **Processor (CPU):** Intel Core i3 / i5 (8th Gen+) or AMD Ryzen 3
* **Memory (RAM):** 8 GB (Expect high usage during AI tasks)
* **Graphics:** Integrated Graphics (Intel HD / AMD Vega)
* **Storage:** 10 GB free space (For environments and AI models)

### 🚀 Recommended Requirements (Runs on GPU - Lightning Fast)
* **OS:** Windows 10 / Windows 11 (64-bit)
* **Processor (CPU):** Intel Core i5 / i7 (10th Gen+) or AMD Ryzen 5 / 7
* **Memory (RAM):** 16 GB or higher
* **Graphics (GPU):** **NVIDIA GPU** (GTX 1660, RTX 2060, RTX 3050 or better) with at least 4GB+ VRAM. *CUDA acceleration is automatically detected and utilized.*
* **Storage:** SSD with 15 GB free space.

---

## 🛠️ Installation Guide (One-Click Setup)

Forget complicated command lines. G-Toolbox comes with automated setup scripts.

**Step 1: Download the Project**
Clone this repository or download it as a ZIP file and extract it to a folder on your PC.

**Step 2: Install Dependencies**
Double-click the `installation.bat` file. 
* This will automatically create an isolated Python Virtual Environment (`venv`) so it doesn't mess with your computer's global Python settings. 
* It will download all necessary packages (PyTorch, FastAPI, etc.). *Note: This may take 5-15 minutes depending on your internet speed.*

**Step 3: Launch the App**
Double-click the `Start.bat` file.
* This will start the local server. A terminal window will open—leave it running in the background.
* Open your web browser and go to: `http://localhost:8000`

**Step 4: Clean Uninstall (Optional)**
If you ever want to completely remove G-Toolbox and reclaim your disk space, do not just delete the folder! Double-click `DELETE.bat`.
* This will safely delete the virtual environment AND locate the hidden AI model cache files (which can be gigabytes in size) stored deep in your Windows user folders, ensuring a 100% clean removal.
