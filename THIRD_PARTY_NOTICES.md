# Third-party notices

G-Toolbox itself is licensed under [CC BY-NC 4.0](LICENSE). It bundles or downloads the
third-party components below, each under its own license. Always check the linked project
for the authoritative license text.

## Shipped inside this repository / every package

| Component | Where | License |
| :--- | :--- | :--- |
| [Tailwind CSS](https://github.com/tailwindlabs/tailwindcss) 3.4.17 (generated CSS) | `static/vendor/tailwind.css` | MIT |
| [Font Awesome Free](https://fontawesome.com/license/free) 6.5.1 | `static/vendor/fontawesome/` | Icons CC BY 4.0, fonts SIL OFL 1.1, code MIT (see `LICENSE.txt` there) |
| [Inter](https://github.com/rsms/inter) and [JetBrains Mono](https://github.com/JetBrains/JetBrainsMono) via [Fontsource](https://fontsource.org) | `static/vendor/fonts/` | SIL Open Font License 1.1 (license files included) |
| [qrcode-generator](https://github.com/kazuhikoarase/qrcode-generator) 1.4.4 | `static/vendor/qrcode/qrcode.js` | MIT (header in file). "QR Code" is a registered trademark of DENSO WAVE INCORPORATED |

## Python dependencies

Installed from PyPI at the exact versions in `requirements-*.lock` (core) or on demand
(`requirements-ai.txt`). Main ones: FastAPI, Starlette, Uvicorn, Pydantic (MIT), Jinja2
(BSD-3-Clause), Pillow (MIT-CMU), pypdf (BSD-3-Clause), pyAesCrypt (Apache-2.0),
yt-dlp (Unlicense), ffmpeg-python (Apache-2.0), psutil (BSD-3-Clause), certifi (MPL-2.0),
pywebview (BSD-3-Clause). AI engines: PyTorch (BSD-3-Clause), Real-ESRGAN (BSD-3-Clause),
BasicSR (Apache-2.0), rembg (MIT), faster-whisper (MIT), Demucs (MIT),
simple-lama-inpainting (see its project page).

## Linux AppImage only

| Component | License |
| :--- | :--- |
| [python-build-standalone](https://github.com/astral-sh/python-build-standalone) CPython 3.11 | PSF License plus the licenses of the libraries it links (listed in the distribution) |
| [FFmpeg](https://ffmpeg.org) static build from [BtbN/FFmpeg-Builds](https://github.com/BtbN/FFmpeg-Builds) | **GPL** (this build includes GPL components such as x264). Unmodified; source: ffmpeg.org and the BtbN repository. License copy in `usr/share/licenses/ffmpeg/` inside the AppImage |
| [AppImage type2 runtime](https://github.com/AppImage/type2-runtime) | MIT |

## Model weights (downloaded on demand, never bundled)

| Model | Source | License |
| :--- | :--- | :--- |
| RealESRGAN_x4plus, RealESRGAN_x4plus_anime_6B | [xinntao/Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) | BSD-3-Clause |
| big-lama | [advimman/lama](https://github.com/advimman/lama) via simple-lama-inpainting | Apache-2.0 |
| u2net | [xuebinqin/U-2-Net](https://github.com/xuebinqin/U-2-Net) via rembg | Apache-2.0 |
| Whisper models (CTranslate2 conversions) | [OpenAI Whisper](https://github.com/openai/whisper) / [Systran](https://huggingface.co/Systran) | MIT |
| htdemucs | [facebookresearch/demucs](https://github.com/facebookresearch/demucs) | MIT |

## Android app

AndroidX and Material Components (Apache-2.0); Google Play services code scanner
(Google APIs Terms of Service).
