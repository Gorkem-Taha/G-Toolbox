# 📦 G-Toolbox v4.3.0 Release Binaries

Bu dizin, G-Toolbox v4.3.0 sürümüne ait taşınabilir Linux AppImage ve Android APK dağıtım paketlerini içerir.

---

## 📁 Paket Listesi & SHA-256 Doğrulama Özetleri

| Dosya Adı | Hedef Platform | Boyut | Mimari / Tür | SHA-256 Özeti (Checksum) |
| :--- | :--- | :--- | :--- | :--- |
| **`G-Toolbox-x86_64.AppImage`** | Linux (Ubuntu, Debian, Fedora, Arch) | ~1.15 MB | `x86_64` Standalone Portable | `0f7be770d1b8b5c988cd2accf49f6081ce169b4b43d9d23b7c015fa1bebd3f91` |
| **`G-Toolbox.apk`** | Android (Mobil & Tablet) | ~5.27 MB | `arm64-v8a / armeabi-v7a / x86_64` | `8f897b090c4d7b81fff1b2cbb508ddd74a5dcce84bfcc4a0abb4519725deef8f` |

---

## 🐧 Linux (AppImage) Hızlı Çalıştırma
```bash
chmod +x G-Toolbox-x86_64.AppImage
./G-Toolbox-x86_64.AppImage
```
*Ubuntu 22.04+ ve modern dağıtımlarda FUSE hatası alırsanız:*
```bash
sudo apt install -y libfuse2
# veya FUSE olmadan doğrudan çalıştırmak için:
./G-Toolbox-x86_64.AppImage --appimage-extract-and-run
```

---

## 📱 Android (APK) Kurulumu
1. `G-Toolbox.apk` dosyasını telefonunuza indirin veya USB/Bluetooth ile aktarın.
2. Dosyayı açın ve istendiğinde *"Bilinmeyen kaynaklardan uygulama yükleme"* iznini verin.
3. Uygulamayı başlatın:
   - **PC Sunucu Modu (GPU Hızlandırma):** Bilgisayarınızla aynı Wi-Fi ağına bağlanıp bilgisayar IP'nizi girerek PC'deki RTX/GTX GPU üzerinden 4x AI Upscaling ve medya indirme yapın.
   - **Yerel Mod (Çevrimdışı):** Bilgisayara gerek duymadan telefonunuzun kendi işlemcisiyle offline görsel dönüştürme ve EXIF temizleme yapın.

---

> 🌐 **Resmi GitHub Release Sayfası:** [https://github.com/Gorkem-Taha/G-Toolbox/releases/tag/v4.3.0](https://github.com/Gorkem-Taha/G-Toolbox/releases/tag/v4.3.0)
