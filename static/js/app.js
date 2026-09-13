// ═════════════════════════════════════════════════════════════════
// GLOBAL OPERATING MODE & API ROUTING
// ═════════════════════════════════════════════════════════════════
let currentMode = localStorage.getItem('gtoolbox_mode') || 'pc';
let customServerUrl = localStorage.getItem('gtoolbox_server_url') || '';

// If operating in PC / Local Desktop mode, ensure customServerUrl is cleared
// so all requests strictly route to the local host/port without port mismatch
if (currentMode === 'pc') {
    customServerUrl = '';
    localStorage.removeItem('gtoolbox_server_url');
}

function getApiBaseUrl() {
    // In PC mode or when running via browser/webview directly, ALWAYS use relative path ("")
    // Relative paths ensure 100% reliability regardless of port or LAN IP
    if (currentMode === 'pc' || window.location.protocol.startsWith('http')) {
        if (currentMode === 'mobile' && customServerUrl) {
            return customServerUrl.replace(/\/+$/, '');
        }
        return '';
    }
    if (customServerUrl) {
        return customServerUrl.replace(/\/+$/, '');
    }
    return '';
}

const translations = {
    en: {
        app_title: "G-Toolbox | Premium Toolbox",
        app_desc: "Premium multi-purpose media & file processing tool.",
        app_version: "Toolbox v4.0",
        hero_title: "The Only Place for All Your Files",
        hero_desc: "Process your media, documents, and files locally, securely, and at lightning speed with G-Toolbox. With zero data leak guarantee.",
        menu_converter: "Media Converter",
        desc_converter: "Convert your image, audio, and video files to any format in seconds. No limits, no waiting.",
        menu_bgremover: "Background Remover",
        desc_bgremover: "Flawlessly remove the background of your photos with advanced AI in a single click.",
        menu_videodownloader: "Video Downloader",
        desc_videodownloader: "Download videos from YouTube and other platforms in your desired quality and resolution, watermark-free.",
        menu_magic_eraser: "Magic Eraser",
        desc_magic_eraser: "Professionally erase unwanted objects, people, or text from your images with AI.",
        menu_upscaler: "Resolution Upscaler",
        desc_upscaler: "Make your low-quality photos up to 4X clearer and more detailed with AI.",
        menu_filevault: "Vault Creator",
        desc_filevault: "Create secure locked archives by encrypting your files and folders with military-grade AES-256.",
        menu_separator: "Vocal Separator",
        desc_separator: "Extract vocals and instrumental backing tracks from songs using Demucs AI.",
        menu_transcriber: "AI Transcriber",
        desc_transcriber: "Generate speech-to-text transcripts and SRT subtitles with Faster-Whisper.",
        menu_metadata: "EXIF & Privacy Cleaner",
        desc_metadata: "Inspect and strip GPS tags, camera model, and hidden metadata from photos.",
        menu_animator: "Video to GIF / WebP",
        desc_animator: "Extract video segments into high-quality animated GIFs or lightweight WebP files.",
        menu_subtitles: "Subtitle Burner",
        desc_subtitles: "Burn SRT or VTT subtitles directly into video with custom styling.",
        menu_pdftools: "PDF Toolkit",
        desc_pdftools: "Merge multiple PDFs, extract page ranges, or extract text into TXT.",
        menu_audiofx: "Audio Effects & Speed",
        desc_audiofx: "Slowed+Reverb, Nightcore, speed, tempo, and pitch manipulation.",
        menu_noisecleaner: "Noise Cleaner",
        desc_noisecleaner: "Remove background hiss, fan noise, and hum with adaptive FFT noise filtering.",
        btn_purge_vram: "Purge VRAM",
        btn_go_tool: "Go to Tool",
        sidebar_tools: "Tools",
        sidebar_footer: "All files are processed locally",
        welcome_title: "Welcome",
        welcome_subtitle: "Select a tool from the left menu to start",
        global_progress_starting: "Starting process...",
        drop_file_here: "Drop Your File Here",
        drop_or_click: "or click to browse",
        target_format: "Select Target Format",
        search_format_placeholder: "Search target format...",
        btn_start_conversion: "Start Magic Conversion!",
        drop_image_here: "Drop Your Image Here",
        drop_or_click_image: "or click to select",
        brush_size: "Brush:",
        btn_clear: "Clear",
        btn_close: "Close",
        btn_magic_erase: "Erase Magically!",
        select_upscale_ratio: "Select Upscale Ratio",
        hd_quality: "HD Quality - Fast process",
        "4k_quality": "4K Quality - Maximum detail",
        upscale_processing: "AI is increasing pixels and sharpening...",
        process_takes_time: "This process may take a while",
        btn_start_upscale: "Start Magic Upscaling!",
        drop_bg_image: "Drag the image you want to remove the background from",
        drop_or_click_image_bg: "or click to select an image",
        badge_image: "Image",
        preview_original: "Original",
        preview_result: "Result",
        ai_processing: "AI is Processing...",
        removing_bg: "Removing background",
        btn_remove_bg: "Magic Remove Background",
        badge_ai_powered: "AI Powered",
        badge_transparent_png: "Transparent PNG Output",
        badge_auto_download: "Auto Download",
        video_link_placeholder: "Paste video link (YouTube, etc.)...",
        btn_fetch_info: "Fetch Info",
        fetching_video_info: "Fetching Video Info...",
        select_resolution: "Select Resolution",
        btn_start_download: "Start Download",
        video_processing: "Video is downloading and processing...",
        process_minutes: "This process may take a few minutes",
        badge_youtube_support: "YouTube Supported",
        badge_mp3_convert: "MP3 Conversion",
        badge_high_quality: "High Quality",
        vault_title: "Vault Creator (AES-256)",
        vault_desc: "Lock or decrypt your files via military-grade encryption.",
        vault_mode_file: "Select File",
        vault_mode_dir: "Select Folder",
        vault_drop_text: "Drop your files or folders here",
        vault_drop_click: "or click to select",
        btn_vault_clear: "Clear Selection",
        vault_pwd_placeholder: "Set / enter a secure password",
        btn_vault_encrypt: "Encrypt File",
        btn_vault_decrypt: "Unlock (Decrypt)",
        btn_sync_update: "🔄 Update System (Sync)",
        update_success_title: "Update Complete!",
        update_success_desc: "Please close the black screen (terminal) and restart the application for the changes to take effect.",

        // Tools 7-14 UI Keys
        separation_mode: "Separation Mode",
        separator_drop_title: "Drop Audio or Video File Here",
        separator_drop_sub: "or click to browse (MP3, WAV, MP4, etc.)",
        separator_2stems: "🎤 2 Stem (Vocals + Backing Track)",
        separator_4stems: "🥁 4 Stem (Vocals, Drums, Bass, Other)",
        btn_separate_stems: "Separate Vocals & Music",

        transcriber_drop_title: "Drop Media to Transcribe",
        transcriber_drop_sub: "Select audio or video file",
        transcriber_output_format: "Output Format",
        transcriber_format_txt: "📄 Plain Text (.txt)",
        transcriber_format_srt: "🎬 Subtitles with Timestamps (.srt)",
        transcriber_format_json: "🔍 Structured JSON (.json)",
        transcriber_lang_label: "Language Selection",
        transcriber_lang_auto: "🌐 Auto Detect (Auto)",
        transcriber_btn_apply: "Generate Transcript / Subtitles",
        transcriber_preview: "Preview:",
        btn_copy: "Copy",

        metadata_drop_title: "Drop Photo to Strip Privacy Metadata",
        metadata_drop_sub: "Supports JPG, PNG, WebP, and TIFF",
        metadata_btn_inspect: "Scan Tags",
        metadata_btn_strip: "Reset EXIF & Download",
        metadata_detected_title: "Detected Metadata:",

        anim_drop_title: "Drop Video to Convert into Animation",
        anim_drop_sub: "Supports MP4, MOV, MKV, WebM",
        anim_label_start: "Start (sec / 00:00:00)",
        anim_label_duration: "Duration (seconds)",
        anim_label_fps: "FPS (Frame Rate)",
        anim_label_width: "Width (px)",
        anim_btn_gif: "🎞️ High Quality GIF",
        anim_btn_webp: "🚀 Optimized WebP (Smaller)",
        anim_btn_apply: "Generate Animation & Download",

        sub_title_video: "1. Select Video File",
        sub_video_types: "MP4, MKV, MOV, WebM",
        sub_title_sub: "2. Subtitle File (.srt, .vtt)",
        sub_sub_types: "SRT, VTT, or ASS",
        sub_fontsize_label: "Font Size",
        sub_fontcolor_label: "Font Color",
        sub_opt_small: "Small (18px)",
        sub_opt_standard: "Standard / Normal (24px)",
        sub_opt_large: "Large (32px)",
        sub_opt_xlarge: "Extra Large (40px)",
        sub_color_white: "⚪ White (Classic)",
        sub_color_yellow: "🟡 Yellow (Cinematic)",
        sub_color_cyan: "🔵 Cyan",
        sub_color_green: "🟢 Light Green",
        sub_apply_btn: "Burn Subtitles & Download",

        pdf_tab_merge: "Merge",
        pdf_tab_split: "Split",
        pdf_tab_text: "Extract Text",
        pdf_merge_drop_title: "Drop PDFs to Merge",
        pdf_merge_drop_sub: "Select multiple PDFs (Order is preserved)",
        pdf_merge_btn: "Merge All PDFs into Single File",
        pdf_split_drop_title: "Drop PDF File to Split",
        pdf_split_drop_sub: "Select a single PDF file",
        pdf_split_label: "Pages / Ranges to Extract:",
        pdf_split_placeholder: "e.g. 1-3, 5, 8-10 or just 2-4",
        pdf_split_hint: "Ranges can be comma separated. E.g.: '1-5' (first 5 pages) or '1,3,7'.",
        pdf_split_btn: "Extract Selected Pages as New PDF",
        pdf_text_drop_title: "Drop PDF to Extract Text",
        pdf_text_drop_sub: "All page text is converted into digital TXT format",
        pdf_text_btn: "Extract Text from PDF",
        pdf_text_preview: "Extracted Text Preview:",
        btn_download_txt: ".txt Download",

        fx_drop_title: "Drop Audio or Video to Apply Effects",
        fx_drop_sub: "Supports MP3, WAV, FLAC, M4A, MP4",
        fx_presets_label: "Quick Presets",
        fx_tempo_label: "Tempo / Speed:",
        fx_pitch_label: "Pitch:",
        fx_reverb_title: "Echo & Reverb Effect",
        fx_reverb_desc: "Adds spatial depth and cinematic acoustic ambience",
        fx_apply_btn: "Generate Audio with Effects & Download",
        fx_slow: "Slow",
        fx_fast: "Fast",
        fx_deep: "Deep",
        fx_high: "High",

        noise_drop_title: "Drop Media to Clean Noise",
        noise_drop_sub: "Cleans mic hiss, fan noise, and background hum",
        noise_strength_label: "Noise Reduction Strength:",
        noise_voice_focus_title: "Voice Focus & Clarity",
        noise_voice_focus_desc: "Cuts deep rumble and emphasizes speech frequencies",
        noise_apply_btn: "Clean Noise & Download",
        noise_light: "Light",
        noise_balanced: "Balanced",
        noise_heavy: "Heavy Filter",

        // Device Mode Modal
        device_modal_title: "Operating Mode & Mobile Link",
        device_modal_subtitle: "Mobile device and desktop connection configuration",
        badge_recommended: "Recommended",
        badge_offline: "Offline",
        mode_pc_title: "PC Server",
        mode_pc_desc: "Processes AI Upscaling, 4K video, and FFmpeg on your PC's GPU.",
        mode_local_title: "Local Device",
        mode_local_desc: "Uses mobile browser CPU. Basic media tools work even when PC is off.",
        label_pc_url: "PC Server URL (LAN / Wi-Fi or Tunnel):",
        btn_test_conn: "Test",
        title_mobile_qr: "To Open on Mobile Phone:",
        desc_mobile_qr: "Type this address in your phone browser on the same Wi-Fi:",
        title_local_active: "Phone CPU Active",
        desc_local_active: "Images are processed directly in your mobile browser (HTML5 Canvas). No server or internet needed.",
        cap_img_convert: "Image Format Conversion",
        cap_img_compress: "Image Compression",
        cap_exif_clean: "EXIF Cleaning",
        cap_heavy_ai: "Heavy AI (Requires PC)",
        btn_save_apply: "Save & Apply",

        // Dynamic messages
        processing: "Processing...",
        completed: "Completed!",
        failed: "Failed!",
        toast_success: "Success!",
        toast_error: "Error!",
        toast_info: "Info",
        connecting: "Connecting...",
        poll_failed: "Progress poll failed",
        unsupported_format: "This file format is not supported yet.",
        no_format_found: "No such format found.",
        converting: "Converting...",
        conversion_failed: "Conversion failed.",
        conversion_success: "Conversion Successful!",
        select_image_error: "Please select an image file.",
        erasing_ai: "AI is Processing...",
        erase_success: "Magic erase completed, image is downloading! You can draw again.",
        erase_failed: "Magic erase failed.",
        magic_erase_btn: "Magic Erase!",
        pixel_upscale_success: "Pixel Upscale Successful!",
        fetch_success: "Video info fetched successfully!",
        fetch_error: "Video info could not be retrieved.",
        url_error: "Please enter a video link.",
        download_started: "Starting...",
        downloading_pct: "Downloading... %",
        merge_processing: "Merging and converting...",
        download_success: "Download Successful!",
        download_failed: "Download failed.",
        server_error: "Server connection error.",
        vault_encrypt_btn: "Encrypt File",
        vault_encrypt_folder_btn: "Encrypt Folder",
        vault_decrypt_btn: "Unlock (Decrypt)",
        vault_drop_file_title: "Drop your files or folders here",
        vault_drop_folder_title: "Drop Your Folder Here",
        vault_drop_hint_file: 'or click to <span class="text-purple-400 font-medium hover:underline">select</span>',
        vault_drop_hint_folder: 'For <b>encrypting</b> folders only.<br/><span class="text-xs text-purple-400 mt-1 block">Switch to File mode to unlock (.enc).</span>',
        folder_selected: "items selected",
        total_size: "Total:",
        enter_password: "Please enter a password!",
        encrypting_data: "Processing and Encrypting data...",
        encrypt_success: "Encryption Successful!",
        decrypt_success: "Unlocked!",
        wrong_password: "Incorrect password or corrupted file!",
        vault_action_failed: "Action failed.",
        best_quality: "Best Quality",
        only_audio: "Audio Only (MP3)",

        select_pdf_error: "Please select a PDF file.",
        select_sub_error: "Please select a subtitle file (.srt, .vtt).",
        select_video_error: "Please select a video file.",
        select_audio_video_error: "Please select an audio or video file.",
        select_two_pdf_error: "Please select at least 2 PDFs to merge.",
        select_split_pdf_error: "Please select a PDF file to split.",
        select_split_pages_error: "Please enter page numbers or ranges (e.g. 1-3).",
        select_inspect_img_error: "Please select an image to inspect.",
        copied_to_clipboard: "Copied to clipboard!",
        vram_purge_success: "VRAM and models successfully purged!",
        vram_purge_failed: "VRAM purge request failed.",
        download_started_short: "Download started...",
        preset_slowed_loaded: "Slowed + Reverb preset loaded",
        preset_nightcore_loaded: "Nightcore preset loaded",
        preset_fast_loaded: "1.25x Fast preset loaded",
        preset_reset_loaded: "Standard (1.0x) preset loaded"
    },
    tr: {
        app_title: "G-Toolbox | Premium Araç Seti",
        app_desc: "Premium çok amaçlı medya & dosya işleme aracı.",
        app_version: "Araç Seti v4.0",
        hero_title: "Tüm Dosyalarınız İçin Tek Yer",
        hero_desc: "Medya, belge ve dosyalarınızı G-Toolbox ile yerel, güvenli ve ışık hızında işleyin. Sıfır veri sızıntısı garantisiyle.",
        menu_converter: "Medya Dönüştürücü",
        desc_converter: "Resim, ses ve video dosyalarınızı saniyeler içinde herhangi bir formata dönüştürün. Limit yok, bekleme yok.",
        menu_bgremover: "Arka Plan Silici",
        desc_bgremover: "Gelişmiş yapay zeka ile fotoğraflarınızın arka planını tek tıkla kusursuzca kaldırın.",
        menu_videodownloader: "Video İndirici",
        desc_videodownloader: "YouTube ve diğer platformlardan videoları istediğiniz kalite ve çözünürlükte, filigransız indirin.",
        menu_magic_eraser: "Sihirli Silgi",
        desc_magic_eraser: "İstemediğiniz objeleri, kişileri veya metinleri yapay zeka ile fotoğraflarınızdan profesyonelce silin.",
        menu_upscaler: "Çözünürlük Yükseltici",
        desc_upscaler: "Düşük kaliteli fotoğraflarınızı yapay zeka ile 4 kata kadar daha net ve detaylı hale getirin.",
        menu_filevault: "Kasa Oluşturucu",
        desc_filevault: "Dosya ve klasörlerinizi askeri düzeyde AES-256 ile şifreleyerek güvenli kilitli arşivler oluşturun.",
        menu_separator: "Vokal Ayırıcı",
        desc_separator: "Demucs yapay zekası ile şarkılardan vokal ve enstrümantal altyapıları ayrıştırın.",
        menu_transcriber: "YZ Transkript & Altyazı",
        desc_transcriber: "Faster-Whisper ile video ve seslerden anında metin veya SRT altyazısı üretin.",
        menu_metadata: "EXIF & Gizlilik Temizleyici",
        desc_metadata: "Fotoğraflardaki GPS konumunu, cihaz modelini ve gizli metaverileri temizleyin.",
        menu_animator: "Video to GIF / WebP",
        desc_animator: "Videolardan zaman aralığı seçerek yüksek kaliteli GIF veya WebP animasyonları oluşturun.",
        menu_subtitles: "Altyazı Gömücü",
        desc_subtitles: "SRT veya VTT altyazılarını özel font ve stil ayarlarıyla videoya kalıcı olarak gömün.",
        menu_pdftools: "PDF Araç Seti",
        desc_pdftools: "Çoklu PDF birleştirme, sayfa bölme/ayırma ve metin çıkarma işlemleri.",
        menu_audiofx: "Ses Efektleri & Hız",
        desc_audiofx: "Slowed+Reverb, Nightcore, tempo ve perde değiştirme efektleri uygulayın.",
        menu_noisecleaner: "Dip Gürültü Temizleyici",
        desc_noisecleaner: "Adaptif FFT filtreleme ile dip gürültü, dip ses ve fan uğultularını temizleyin.",
        btn_purge_vram: "VRAM Boşalt",
        btn_go_tool: "Araca Git",
        sidebar_tools: "Araçlar",
        sidebar_footer: "Tüm dosyalar yerel olarak işlenir",
        welcome_title: "Hoş Geldiniz",
        welcome_subtitle: "Başlamak için sol menüden bir araç seçin",
        global_progress_starting: "İşlem başlatılıyor...",
        drop_file_here: "Dosyanızı Buraya Bırakın",
        drop_or_click: "veya seçmek için tıklayın",
        target_format: "Hedef Formatı Seçin",
        search_format_placeholder: "Hedef format ara...",
        btn_start_conversion: "Sihirli Dönüştürmeyi Başlat!",
        drop_image_here: "Resminizi Buraya Bırakın",
        drop_or_click_image: "veya seçmek için tıklayın",
        brush_size: "Fırça:",
        btn_clear: "Temizle",
        btn_close: "Kapat",
        btn_magic_erase: "Sihirle Sil!",
        select_upscale_ratio: "Büyütme Oranını Seçin",
        hd_quality: "HD Kalite - Hızlı işlem",
        "4k_quality": "4K Kalite - Maksimum detay",
        upscale_processing: "YZ pikselleri artırıyor ve keskinleştiriyor...",
        process_takes_time: "Bu işlem biraz sürebilir",
        btn_start_upscale: "Sihirli Büyütmeyi Başlat!",
        drop_bg_image: "Arka planını silmek istediğiniz resmi sürükleyin",
        drop_or_click_image_bg: "veya resim seçmek için tıklayın",
        badge_image: "Resim",
        preview_original: "Orijinal",
        preview_result: "Sonuç",
        ai_processing: "YZ İşliyor...",
        removing_bg: "Arka plan kaldırılıyor",
        btn_remove_bg: "Sihirli Arka Planı Kaldır",
        badge_ai_powered: "YZ Destekli",
        badge_transparent_png: "Şeffaf PNG Çıktısı",
        badge_auto_download: "Otomatik İndirme",
        video_link_placeholder: "Video linkini yapıştırın (YouTube vb.)...",
        btn_fetch_info: "Bilgileri Getir",
        fetching_video_info: "Video Bilgileri Getiriliyor...",
        select_resolution: "Çözünürlük Seçin",
        btn_start_download: "İndirmeyi Başlat",
        video_processing: "Video indiriliyor ve işleniyor...",
        process_minutes: "Bu işlem birkaç dakika sürebilir",
        badge_youtube_support: "YouTube Destekli",
        badge_mp3_convert: "MP3 Dönüştürme",
        badge_high_quality: "Yüksek Kalite",
        vault_title: "Kasa Oluşturucu (AES-256)",
        vault_desc: "Dosyalarınızı askeri düzeyde şifreleme ile kilitleyin veya şifresini çözün.",
        vault_mode_file: "Dosya Seç",
        vault_mode_dir: "Klasör Seç",
        vault_drop_text: "Dosyalarınızı veya klasörlerinizi buraya bırakın",
        vault_drop_click: "veya seçmek için tıklayın",
        btn_vault_clear: "Seçimi Temizle",
        vault_pwd_placeholder: "Güvenli bir şifre belirleyin / girin",
        btn_vault_encrypt: "Dosyayı Şifrele",
        btn_vault_decrypt: "Kilidi Aç (Şifre Çöz)",
        btn_sync_update: "🔄 Sistemi Güncelle (Sync)",
        update_success_title: "Güncelleme Tamamlandı!",
        update_success_desc: "Değişikliklerin aktif olması için lütfen siyah ekranı (terminali) kapatıp uygulamayı yeniden başlatın.",

        // Tools 7-14 UI Keys
        separation_mode: "Ayrıştırma Modu",
        separator_drop_title: "Ses veya Video Dosyasını Buraya Bırakın",
        separator_drop_sub: "veya seçmek için tıklayın (MP3, WAV, MP4 vb.)",
        separator_2stems: "🎤 2 Stem (Vokal + Altyapı)",
        separator_4stems: "🥁 4 Stem (Vokal, Davul, Bas, Diğer)",
        btn_separate_stems: "Vokalleri ve Müziği Ayrıştır",

        transcriber_drop_title: "Transkript Edilecek Medyayı Bırakın",
        transcriber_drop_sub: "Video veya ses dosyasını seçin",
        transcriber_output_format: "Çıktı Formatı",
        transcriber_format_txt: "📄 Düz Metin (.txt)",
        transcriber_format_srt: "🎬 Zaman Damgalı Altyazı (.srt)",
        transcriber_format_json: "🔍 Yapılandırılmış JSON (.json)",
        transcriber_lang_label: "Dil Seçimi",
        transcriber_lang_auto: "🌐 Otomatik Algıla (Auto)",
        transcriber_btn_apply: "Transkript / Altyazıyı Çıkar",
        transcriber_preview: "Önizleme:",
        btn_copy: "Kopyala",

        metadata_drop_title: "Gizliliği Temizlenecek Fotoğrafı Bırakın",
        metadata_drop_sub: "JPG, PNG, WebP ve TIFF desteklenir",
        metadata_btn_inspect: "Etiketleri Tara",
        metadata_btn_strip: "EXIF'i Sıfırla & İndir",
        metadata_detected_title: "Tespit Edilen Metaveriler:",

        anim_drop_title: "Animasyona Dönüştürülecek Videoyu Bırakın",
        anim_drop_sub: "MP4, MOV, MKV, WebM desteklenir",
        anim_label_start: "Başlangıç (sn / 00:00:00)",
        anim_label_duration: "Süre (saniye)",
        anim_label_fps: "FPS (Kare Hızı)",
        anim_label_width: "Genişlik (px)",
        anim_btn_gif: "🎞️ Yüksek Kalite GIF",
        anim_btn_webp: "🚀 Optimize WebP (Daha Küçük)",
        anim_btn_apply: "Animasyonu Üret ve İndir",

        sub_title_video: "1. Video Dosyası Seçin",
        sub_video_types: "MP4, MKV, MOV, WebM",
        sub_title_sub: "2. Altyazı Dosyası (.srt, .vtt)",
        sub_sub_types: "SRT, VTT veya ASS",
        sub_fontsize_label: "Yazı Boyutu (Font Size)",
        sub_fontcolor_label: "Yazı Rengi",
        sub_opt_small: "Küçük (18px)",
        sub_opt_standard: "Standart / Normal (24px)",
        sub_opt_large: "Büyük (32px)",
        sub_opt_xlarge: "Çok Büyük (40px)",
        sub_color_white: "⚪ Beyaz (Klasik)",
        sub_color_yellow: "🟡 Sarı (Sinematik)",
        sub_color_cyan: "🔵 Camgöbeği (Cyan)",
        sub_color_green: "🟢 Açık Yeşil",
        sub_apply_btn: "Altyazıyı Videoya Kalıcı Göm ve İndir",

        pdf_tab_merge: "Birleştir",
        pdf_tab_split: "Sayfa Böl",
        pdf_tab_text: "Metin Çıkar",
        pdf_merge_drop_title: "Birleştirilecek PDF'leri Bırakın",
        pdf_merge_drop_sub: "Birden fazla PDF seçebilirsiniz (Sıralama otomatik korunur)",
        pdf_merge_btn: "Tüm PDF'leri Tek Dosyada Birleştir",
        pdf_split_drop_title: "Bölünecek PDF Dosyasını Bırakın",
        pdf_split_drop_sub: "Tek bir PDF dosyası seçin",
        pdf_split_label: "Çıkarılacak Sayfalar / Aralıklar:",
        pdf_split_placeholder: "Örn: 1-3, 5, 8-10 veya sadece 2-4",
        pdf_split_hint: "Aralıklar virgülle ayrılabilir. Örnek: '1-5' (ilk 5 sayfa) veya '1,3,7'.",
        pdf_split_btn: "Seçili Sayfaları Yeni PDF Olarak Çıkar",
        pdf_text_drop_title: "Metni Çıkarılacak PDF'i Bırakın",
        pdf_text_drop_sub: "Tüm sayfalardaki metinler dijital TXT formatına dönüştürülür",
        pdf_text_btn: "PDF'teki Metinleri Çıkar",
        pdf_text_preview: "Çıkarılan Metin Önizleme:",
        btn_download_txt: ".txt İndir",

        fx_drop_title: "Efekt Uygulanacak Ses veya Videoyu Bırakın",
        fx_drop_sub: "MP3, WAV, FLAC, M4A, MP4 desteklenir",
        fx_presets_label: "Hızlı Hazır Ayarlar (Presets)",
        fx_tempo_label: "Tempo / Hız:",
        fx_pitch_label: "Perde / Pitch:",
        fx_reverb_title: "Yankı & Reverb Efekti",
        fx_reverb_desc: "Uzaysal derinlik ve sinematik akustik ambiyans katar",
        fx_apply_btn: "Efektli Sesi Üret ve İndir",
        fx_slow: "Yavaş",
        fx_fast: "Hızlı",
        fx_deep: "Kalın",
        fx_high: "İnce",

        noise_drop_title: "Dip Gürültüsü Temizlenecek Medyayı Bırakın",
        noise_drop_sub: "Mikrofon hışırtısı, fan sesi, klima uğultusu temizlenir",
        noise_strength_label: "Gürültü Bastırma Gücü (Noise Reduction):",
        noise_voice_focus_title: "İnsan Sesi Netleştirme (Voice Focus)",
        noise_voice_focus_desc: "Derin bas uğultularını keser, konuşma frekanslarını öne çıkarır",
        noise_apply_btn: "Gürültüyü Temizle ve İndir",
        noise_light: "Hafif",
        noise_balanced: "Dengeli",
        noise_heavy: "Yoğun Filtre",

        // Device Mode Modal
        device_modal_title: "Çalışma Modu & Mobil Bağlantı",
        device_modal_subtitle: "Mobil cihaz ve masaüstü bağlantı yapılandırması",
        badge_recommended: "Önerilen",
        badge_offline: "Çevrimdışı",
        mode_pc_title: "PC Sunucusu",
        mode_pc_desc: "Tüm AI Upscale, 4K Video ve FFmpeg işlemlerini bilgisayarınızın GPU'su yürütür.",
        mode_local_title: "Yerel Cihaz",
        mode_local_desc: "Telefonunuzun işlemcisini kullanır. PC kapalıyken bile temel medya araçları çalışır.",
        label_pc_url: "PC Sunucu Adresi (LAN / Wi-Fi veya Tünel):",
        btn_test_conn: "Test Et",
        title_mobile_qr: "Telefonda Açmak İçin:",
        desc_mobile_qr: "Aynı Wi-Fi ağındaki telefonunuzun tarayıcısına bu adresi yazın:",
        title_local_active: "Telefon İşlemcisi Devrede",
        desc_local_active: "Bu modda görseller doğrudan telefonunuzun tarayıcısında (HTML5 Canvas) işlenir. Sunucu veya internet bağlantısına gerek yoktur.",
        cap_img_convert: "Görsel Format Dönüştürme",
        cap_img_compress: "Görsel Sıkıştırma",
        cap_exif_clean: "EXIF Temizleme",
        cap_heavy_ai: "Ağır AI (PC Gerekir)",
        btn_save_apply: "Kaydet ve Uygula",

        // Dynamic messages
        processing: "İşleniyor...",
        completed: "Tamamlandı!",
        failed: "Başarısız!",
        toast_success: "Başarılı!",
        toast_error: "Hata!",
        toast_info: "Bilgi",
        connecting: "Bağlanıyor...",
        poll_failed: "İlerleme sorgusu başarısız oldu",
        unsupported_format: "Bu dosya formatı henüz desteklenmiyor.",
        no_format_found: "Böyle bir format bulunamadı.",
        converting: "Dönüştürülüyor...",
        conversion_failed: "Dönüştürme işlemi başarısız oldu.",
        conversion_success: "Dönüşüm Başarılı!",
        select_image_error: "Lütfen bir resim dosyası seçin.",
        erasing_ai: "Yapay Zeka İşliyor...",
        erase_success: "Sihirli silme tamamlandı, resim indiriliyor! Tekrar çizebilirsiniz.",
        erase_failed: "Sihirli silme hatası.",
        magic_erase_btn: "Sihirle Temizle!",
        pixel_upscale_success: "Piksel Yükseltme Başarılı!",
        fetch_success: "Video bilgileri başarıyla getirildi!",
        fetch_error: "Video bilgisi alınamadı.",
        url_error: "Lütfen bir video linki girin.",
        download_started: "Başlatılıyor...",
        downloading_pct: "İndiriliyor... %",
        merge_processing: "Birleştirme ve dönüştürme yapılıyor...",
        download_success: "İndirme Başarılı!",
        download_failed: "İndirme başarısız.",
        server_error: "Sunucu bağlantı hatası.",
        vault_encrypt_btn: "Dosyayı Şifrele",
        vault_encrypt_folder_btn: "Klasörü Şifrele",
        vault_decrypt_btn: "Kilidi Aç (Şifre Çöz)",
        vault_drop_file_title: "Dosyalarınızı veya klasörlerinizi buraya bırakın",
        vault_drop_folder_title: "Klasörünüzü Buraya Bırakın",
        vault_drop_hint_file: 'veya <span class="text-purple-400 font-medium hover:underline">seçmek için tıklayın</span>',
        vault_drop_hint_folder: 'Sadece klasörleri <b>şifrelemek</b> içindir.<br/><span class="text-xs text-purple-400 mt-1 block">Kilidi açmak (.enc) için Dosya moduna geçin.</span>',
        folder_selected: "eleman seçildi",
        total_size: "Toplam:",
        enter_password: "Lütfen bir şifre girin!",
        encrypting_data: "Veriler İşleniyor ve Şifreleniyor...",
        encrypt_success: "Şifreleme Başarılı!",
        decrypt_success: "Şifre Çözüldü!",
        wrong_password: "Şifre yanlış veya dosya bozuk!",
        vault_action_failed: "İşlem başarısız oldu.",
        best_quality: "En İyi Kalite",
        only_audio: "Sadece Ses (MP3)",

        select_pdf_error: "Lütfen bir PDF dosyası seçin.",
        select_sub_error: "Lütfen bir altyazı (.srt, .vtt) dosyası seçin.",
        select_video_error: "Lütfen bir video dosyası seçin.",
        select_audio_video_error: "Lütfen bir ses veya video dosyası seçin.",
        select_two_pdf_error: "Lütfen birleştirmek için en az 2 PDF seçin.",
        select_split_pdf_error: "Lütfen bölünecek bir PDF dosyası seçin.",
        select_split_pages_error: "Lütfen çıkarılacak sayfa veya aralıkları girin (Örn: 1-3).",
        select_inspect_img_error: "Lütfen incelenecek bir görsel seçin.",
        copied_to_clipboard: "Metin panoya kopyalandı!",
        vram_purge_success: "VRAM ve modeller başarıyla boşaltıldı!",
        vram_purge_failed: "VRAM boşaltma isteği başarısız oldu.",
        download_started_short: "İndirme başlatılıyor...",
        preset_slowed_loaded: "Slowed + Reverb ayarları yüklendi",
        preset_nightcore_loaded: "Nightcore ayarları yüklendi",
        preset_fast_loaded: "1.25x Hızlı ayarları yüklendi",
        preset_reset_loaded: "Standart (1.0x) ayarları yüklendi"
    }
};

const PAGE_META = {};

let savedLang = localStorage.getItem('gtoolbox_lang');
let currentLang = savedLang || (navigator.language && navigator.language.toLowerCase().startsWith('tr') ? 'tr' : 'en');

function i18n(key) {
    if (translations[currentLang] && translations[currentLang][key]) {
        return translations[currentLang][key];
    }
    if (translations.en && translations.en[key]) {
        return translations.en[key];
    }
    return key;
}

window.changeLanguage = function (lang) {
    currentLang = (lang === 'tr' || lang === 'en') ? lang : 'tr';
    localStorage.setItem('gtoolbox_lang', currentLang);
    document.documentElement.lang = currentLang;

    // Update all elements with data-i18n
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        const val = translations[currentLang] && translations[currentLang][key];
        if (val !== undefined && val !== null) {
            const tag = el.tagName.toLowerCase();
            if (tag === 'input' && (el.type === 'text' || el.type === 'password' || el.type === 'search' || el.type === 'number')) {
                el.placeholder = val;
            } else if (tag === 'meta') {
                el.setAttribute('content', val);
            } else if (tag === 'option') {
                el.textContent = val;
            } else {
                el.innerHTML = val;
            }
        }
    });

    // Update all Language Selector buttons (Home + App View + Mobile)
    document.querySelectorAll('.lang-btn-en, #lang-en').forEach(btn => {
        if (currentLang === 'en') {
            btn.classList.add('text-purple-400', 'font-extrabold');
            btn.classList.remove('opacity-50', 'text-gray-400', 'text-gray-300');
            btn.style.opacity = '1';
        } else {
            btn.classList.remove('text-purple-400', 'font-extrabold');
            btn.classList.add('opacity-50', 'text-gray-400');
            btn.style.opacity = '0.5';
        }
    });

    document.querySelectorAll('.lang-btn-tr, #lang-tr').forEach(btn => {
        if (currentLang === 'tr') {
            btn.classList.add('text-purple-400', 'font-extrabold');
            btn.classList.remove('opacity-50', 'text-gray-400', 'text-gray-300');
            btn.style.opacity = '1';
        } else {
            btn.classList.remove('text-purple-400', 'font-extrabold');
            btn.classList.add('opacity-50', 'text-gray-400');
            btn.style.opacity = '0.5';
        }
    });

    // Update dynamic sections if function is registered
    if (typeof window.updatePAGE_META === 'function') {
        window.updatePAGE_META();
    }
};

document.addEventListener("DOMContentLoaded", () => {
    const spinner = document.getElementById("spinner");
    const toastContainer = document.getElementById("toast-container");
    const pageTitle = document.getElementById("page-title");
    const pageSubtitle = document.getElementById("page-subtitle");

    const globalProgressContainer = document.getElementById("global-progress-container");
    const globalProgressBar = document.getElementById("global-progress-bar");
    const globalProgressMessage = document.getElementById("global-progress-message");
    const globalProgressPercent = document.getElementById("global-progress-percent");

    let globalProgressInterval = null;

    function generateTaskId() {
        return 'task-' + Math.random().toString(36).substr(2, 9) + '-' + Date.now();
    }

    function startGlobalProgress(taskId) {
        if (globalProgressInterval) clearInterval(globalProgressInterval);

        if (globalProgressContainer) {
            globalProgressContainer.classList.remove("hidden");
            globalProgressBar.style.width = "0%";
            globalProgressPercent.textContent = "0%";
            globalProgressMessage.textContent = i18n('connecting');
        }

        globalProgressInterval = setInterval(() => {
            fetch(`${getApiBaseUrl()}/progress/${taskId}`)
                .then(r => r.json())
                .then(data => {
                    if (data && typeof data.progress !== 'undefined') {
                        if (globalProgressBar) globalProgressBar.style.width = data.progress + "%";
                        if (globalProgressPercent) globalProgressPercent.textContent = data.progress + "%";
                        if (data.message && globalProgressMessage) {
                            globalProgressMessage.textContent = data.message;
                        }
                    }
                })
                .catch(e => console.warn("Progress poll failed", e));
        }, 500);
    }

    function stopGlobalProgress(isSuccess = true, msg = i18n('completed')) {
        if (globalProgressInterval) clearInterval(globalProgressInterval);
        globalProgressInterval = null;

        if (isSuccess) {
            if (globalProgressBar) globalProgressBar.style.width = "100%";
            if (globalProgressPercent) globalProgressPercent.textContent = "100%";
            if (globalProgressMessage) globalProgressMessage.textContent = msg;

            setTimeout(() => {
                if (globalProgressContainer) globalProgressContainer.classList.add("hidden");
                if (globalProgressBar) globalProgressBar.style.width = "0%";
            }, 2500);
        } else {
            if (globalProgressContainer) globalProgressContainer.classList.add("hidden");
            if (globalProgressBar) globalProgressBar.style.width = "0%";
        }
    }

    // SIDEBAR NAVIGATION
    const sidebarItems = document.querySelectorAll(".sidebar-item[data-tool]");
    const toolPages = document.querySelectorAll(".tool-page");

    window.updatePAGE_META = function() {
        Object.assign(PAGE_META, {
            converter: { title: i18n('menu_converter'), subtitle: i18n('desc_converter') },
            bgremover: { title: i18n('menu_bgremover'), subtitle: i18n('desc_bgremover') },
            "magic-eraser": { title: i18n('menu_magic_eraser'), subtitle: i18n('desc_magic_eraser') },
            upscaler: { title: i18n('menu_upscaler'), subtitle: i18n('desc_upscaler') },
            videodownloader: { title: i18n('menu_videodownloader'), subtitle: i18n('desc_videodownloader') },
            filevault: { title: i18n('vault_title'), subtitle: i18n('vault_desc') },
            separator: { title: i18n('menu_separator'), subtitle: i18n('desc_separator') },
            transcriber: { title: i18n('menu_transcriber'), subtitle: i18n('desc_transcriber') },
            metadata: { title: i18n('menu_metadata'), subtitle: i18n('desc_metadata') },
            animator: { title: i18n('menu_animator'), subtitle: i18n('desc_animator') },
            subtitles: { title: i18n('menu_subtitles'), subtitle: i18n('desc_subtitles') },
            pdftools: { title: i18n('menu_pdftools'), subtitle: i18n('desc_pdftools') },
            audiofx: { title: i18n('menu_audiofx'), subtitle: i18n('desc_audiofx') },
            noisecleaner: { title: i18n('menu_noisecleaner'), subtitle: i18n('desc_noisecleaner') },
        });

        // If there's an active tool, update the header text immediately
        const activeItem = document.querySelector(".sidebar-item.active");
        if (activeItem) {
            const tool = activeItem.dataset.tool;
            if (PAGE_META[tool]) {
                pageTitle.textContent = PAGE_META[tool].title;
                pageSubtitle.textContent = PAGE_META[tool].subtitle;
            }
        }
    };
    window.updatePAGE_META();
    window.changeLanguage(currentLang);

    sidebarItems.forEach((item) => {
        item.addEventListener("click", () => {
            const tool = item.dataset.tool;
            if (!tool) return;

            // Active state
            document.querySelector(".sidebar-item.active")?.classList.remove("active");
            item.classList.add("active");

            // Show/hide pages
            toolPages.forEach((p) => { p.classList.add("hidden"); p.style.display = ""; });
            const target = document.getElementById(`page-${tool}`);
            if (target) {
                target.classList.remove("hidden");
                target.style.display = "flex";
            }

            // Update header
            const meta = PAGE_META[tool];
            if (meta) {
                pageTitle.textContent = meta.title;
                pageSubtitle.textContent = meta.subtitle;
            }
        });
    });

    const homeView = document.getElementById("home-view");
    const appView = document.getElementById("app-view");
    const btnGoHome = document.getElementById("btn-go-home");
    const btnGoTools = document.querySelectorAll(".btn-go-tool");

    btnGoTools.forEach((btn) => {
        btn.addEventListener("click", () => {
            const targetTool = btn.dataset.target;

            homeView.classList.add("hidden");
            appView.classList.remove("hidden");

            const sidebarBtn = document.querySelector(`.sidebar-item[data-tool="${targetTool}"]`);
            if (sidebarBtn) {
                sidebarBtn.click();
            }
        });
    });

    if (btnGoHome) {
        btnGoHome.addEventListener("click", () => {
            appView.classList.add("hidden");
            homeView.classList.remove("hidden");

            document.querySelector(".sidebar-item.active")?.classList.remove("active");
        });
    }
    const UNIVERSAL_FORMATS = {
        image: {
            title: "Görseller",
            icon: "fa-images",
            color: "text-purple-400",
            formats: [
                { ext: "png", label: "PNG", icon: "fa-image" },
                { ext: "jpg", label: "JPG", icon: "fa-image" },
                { ext: "jpeg", label: "JPEG", icon: "fa-image" },
                { ext: "webp", label: "WEBP", icon: "fa-image" },
                { ext: "gif", label: "GIF", icon: "fa-image" },
                { ext: "svg", label: "SVG", icon: "fa-bezier-curve" },
                { ext: "tiff", label: "TIFF", icon: "fa-image" },
                { ext: "ico", label: "ICO", icon: "fa-image" }
            ]
        },
        video: {
            title: "Videolar",
            icon: "fa-film",
            color: "text-amber-500",
            formats: [
                { ext: "mp4", label: "MP4", icon: "fa-film" },
                { ext: "avi", label: "AVI", icon: "fa-film" },
                { ext: "webm", label: "WEBM", icon: "fa-film" },
                { ext: "mkv", label: "MKV", icon: "fa-film" },
                { ext: "mov", label: "MOV", icon: "fa-film" },
                { ext: "gif", label: "GIF", icon: "fa-image" }
            ]
        },
        audio: {
            title: "Sesler",
            icon: "fa-music",
            color: "text-green-400",
            formats: [
                { ext: "mp3", label: "MP3", icon: "fa-music" },
                { ext: "wav", label: "WAV", icon: "fa-music" },
                { ext: "ogg", label: "OGG", icon: "fa-music" },
                { ext: "flac", label: "FLAC", icon: "fa-music" },
                { ext: "aac", label: "AAC", icon: "fa-music" }
            ]
        },
        document: {
            title: "Belgeler",
            icon: "fa-file-lines",
            color: "text-blue-400",
            formats: [
                { ext: "docx", label: "DOCX", icon: "fa-file-word" },
                { ext: "txt", label: "TXT", icon: "fa-file-lines" },
                { ext: "csv", label: "CSV", icon: "fa-file-csv" },
                { ext: "xlsx", label: "XLSX", icon: "fa-file-excel" },
                { ext: "html", label: "HTML", icon: "fa-file-code" },
                { ext: "md", label: "Markdown", icon: "fa-file-code" }
            ]
        }
    };

    // Conversion Matrix
    const conversionMap = {
        // IMAGE to ...
        'png': ['jpg', 'jpeg', 'webp', 'gif', 'bmp', 'tiff', 'ico', 'svg'],
        'jpg': ['png', 'webp', 'gif', 'bmp', 'tiff'],
        'jpeg': ['png', 'webp', 'gif', 'bmp', 'tiff'],
        'webp': ['png', 'jpg', 'jpeg', 'gif'],
        'gif': ['png', 'jpg', 'jpeg', 'mp4'],
        'bmp': ['png', 'jpg', 'jpeg'],
        'tiff': ['png', 'jpg', 'jpeg'],
        'svg': ['png', 'jpg'],

        // VIDEO to ...
        'mp4': ['avi', 'webm', 'mkv', 'mov', 'gif', 'mp3', 'wav'],
        'avi': ['mp4', 'webm', 'mkv', 'mov', 'mp3'],
        'webm': ['mp4', 'avi', 'mkv', 'mp3'],
        'mkv': ['mp4', 'avi', 'mov', 'mp3'],
        'mov': ['mp4', 'avi', 'webm', 'mp3'],

        // AUDIO to ...
        'mp3': ['wav', 'ogg', 'flac', 'aac'],
        'wav': ['mp3', 'ogg', 'flac'],
        'ogg': ['mp3', 'wav', 'flac'],
        'flac': ['mp3', 'wav', 'aac'],
        'aac': ['mp3', 'wav'],

        // DOCUMENT to ...
        'docx': ['txt'],
        'txt': ['docx'],
        'csv': ['xlsx'],
        'xlsx': ['csv']
    };

    const formatDisplay = {
        'png': { label: "PNG", icon: "fa-image" },
        'jpg': { label: "JPG", icon: "fa-image" },
        'jpeg': { label: "JPEG", icon: "fa-image" },
        'webp': { label: "WEBP", icon: "fa-image" },
        'gif': { label: "GIF", icon: "fa-image" },
        'bmp': { label: "BMP", icon: "fa-image" },
        'tiff': { label: "TIFF", icon: "fa-image" },
        'ico': { label: "ICO", icon: "fa-image" },
        'svg': { label: "SVG", icon: "fa-bezier-curve" },
        'mp4': { label: "MP4", icon: "fa-film" },
        'avi': { label: "AVI", icon: "fa-film" },
        'webm': { label: "WEBM", icon: "fa-film" },
        'mkv': { label: "MKV", icon: "fa-film" },
        'mov': { label: "MOV", icon: "fa-film" },
        'mp3': { label: "MP3", icon: "fa-music" },
        'wav': { label: "WAV", icon: "fa-music" },
        'ogg': { label: "OGG", icon: "fa-music" },
        'flac': { label: "FLAC", icon: "fa-music" },
        'aac': { label: "AAC", icon: "fa-music" },
        'docx': { label: "DOCX", icon: "fa-file-word" },
        'txt': { label: "TXT", icon: "fa-file-lines" },
        'csv': { label: "CSV", icon: "fa-file-csv" },
        'xlsx': { label: "XLSX", icon: "fa-file-excel" }
    };

    // Elements
    const dropUniversal = document.getElementById("drop-zone-universal");
    const inputUniversal = document.getElementById("file-input-universal");
    const infoUniversal = document.getElementById("info-universal");
    const infoUniName = document.getElementById("info-universal-name");
    const infoUniSize = document.getElementById("info-universal-size");
    const infoUniIcon = document.getElementById("info-universal-icon");
    const btnUniversalClear = document.getElementById("btn-universal-clear");

    const colTo = document.getElementById("col-to");
    const listTo = document.getElementById("list-convert-to");
    const searchTo = document.getElementById("search-to");
    const btnUniConvert = document.getElementById("btn-universal-convert");

    let universalSelectedFile = null;
    let universalSourceExt = null;
    let universalSelectedFormatTo = null;

    setupDropZone(dropUniversal, inputUniversal, handleUniFile, (e) => {
        if (e.target.closest("#btn-universal-clear") || e.target.closest("#info-universal")) return true;
    });

    function handleUniFile(file) {
        universalSelectedFile = file;
        const ext = file.name.split(".").pop().toLowerCase();

        infoUniName.textContent = file.name;
        infoUniSize.textContent = formatBytes(file.size);

        if (conversionMap[ext] && conversionMap[ext].length > 0) {
            universalSourceExt = ext;
            infoUniIcon.className = `fa-solid ${formatDisplay[ext] ? formatDisplay[ext].icon : 'fa-file'} file-info-icon text-purple-400`;
            infoUniversal.classList.add("visible");
            colTo.classList.remove("hidden");
            renderTargetList(searchTo.value);

            showToast("success", `✅ ${ext.toUpperCase()} ${i18n('fetch_success')}! ${i18n('target_format')}`);
        } else {
            showToast("error", `⚠️ ${i18n('unsupported_format')}`);
            resetUniversalConverter();
            return;
        }
    }

    function renderTargetList(searchTerm = "") {
        listTo.innerHTML = "";
        universalSelectedFormatTo = null;
        btnUniConvert.classList.add("hidden"); // Format seçilene kadar gizli

        if (!universalSourceExt || !conversionMap[universalSourceExt]) return;

        const allowedFormats = conversionMap[universalSourceExt];

        const filteredFormats = allowedFormats.filter(ext => {
            const data = formatDisplay[ext];
            if (!data) return false;
            if (searchTerm && !data.label.toLowerCase().includes(searchTerm.toLowerCase()) && !ext.toLowerCase().includes(searchTerm.toLowerCase())) return false;
            return true;
        });

        if (filteredFormats.length === 0) {
            listTo.innerHTML = `<p class="text-gray-500 text-sm w-full col-span-2 text-center py-4">${i18n('no_format_found')}</p>`;
            return;
        }

        filteredFormats.forEach(ext => {
            const data = formatDisplay[ext];
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = `uni-format-btn w-full text-left px-4 py-3 rounded-xl border border-white/5 bg-white/5 hover:bg-white/10 transition-all flex items-center gap-3 text-sm font-medium text-gray-300 group`;
            btn.dataset.ext = ext;

            btn.innerHTML = `
                <div class="w-8 h-8 rounded-lg bg-black/30 flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform">
                    <i class="fa-solid ${data.icon} text-gray-400 group-hover:text-white"></i>
                </div>
                <span>${data.label} <span class="text-xs text-gray-600 ml-1">(.${ext})</span></span>
            `;

            btn.addEventListener("click", () => {
                listTo.querySelectorAll(".uni-format-btn").forEach(b => {
                    b.classList.remove("ring-2", "ring-purple-500", "bg-purple-500/20", "text-white", "border-transparent");
                    b.querySelector('i').classList.replace("text-purple-400", "text-gray-400");
                });

                btn.classList.add("ring-2", "ring-purple-500", "bg-purple-500/20", "text-white", "border-transparent");
                btn.querySelector('i').classList.replace("text-gray-400", "text-purple-400");

                universalSelectedFormatTo = ext;
                btnUniConvert.classList.remove("hidden");
                btnUniConvert.classList.remove("opacity-50", "pointer-events-none");
            });

            listTo.appendChild(btn);
        });
    }

    searchTo.addEventListener("input", (e) => renderTargetList(e.target.value));

    btnUniversalClear.addEventListener("click", resetUniversalConverter);

    function resetUniversalConverter() {
        universalSelectedFile = null;
        universalSourceExt = null;
        universalSelectedFormatTo = null;
        inputUniversal.value = "";

        infoUniversal.classList.remove("visible");
        colTo.classList.add("hidden");
        btnUniConvert.classList.add("hidden");
        listTo.innerHTML = "";
        searchTo.value = "";

        if (typeof spinner !== 'undefined' && spinner) {
            spinner.classList.remove("visible");
        }
    }

    // Process Universal Conversion Request
    btnUniConvert.addEventListener("click", () => {
        if (!universalSelectedFile || !universalSelectedFormatTo) return;

        // Offline Client-side Local Mode for Images
        const clientImages = ['png', 'jpg', 'jpeg', 'webp'];
        const srcExt = (universalSelectedFile.name.split('.').pop() || '').toLowerCase();
        if (currentMode === 'local' && clientImages.includes(srcExt) && clientImages.includes(universalSelectedFormatTo)) {
            const img = new Image();
            const objUrl = URL.createObjectURL(universalSelectedFile);
            img.onload = () => {
                const canvas = document.createElement('canvas');
                canvas.width = img.naturalWidth;
                canvas.height = img.naturalHeight;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0);
                const mime = (universalSelectedFormatTo === 'jpg' || universalSelectedFormatTo === 'jpeg') ? 'image/jpeg' : (universalSelectedFormatTo === 'webp' ? 'image/webp' : 'image/png');
                canvas.toBlob((blob) => {
                    URL.revokeObjectURL(objUrl);
                    const sourceName = universalSelectedFile.name.replace(/\.[^.]+$/, "");
                    const outName = `${sourceName}.${universalSelectedFormatTo}`;
                    downloadBlob(blob, outName);
                    showToast("success", `🎉 [Yerel Cihaz] Dönüştürme Tamamlandı: ${outName}`);
                    resetUniversalConverter();
                }, mime, 0.92);
            };
            img.src = objUrl;
            return;
        }

        btnUniConvert.disabled = true;
        btnUniConvert.querySelector('span').textContent = i18n('converting');
        btnUniConvert.querySelector('i').className = "fa-solid fa-circle-notch fa-spin text-white text-xl";

        const taskId = generateTaskId();
        startGlobalProgress(taskId);

        const fd = new FormData();
        fd.append("file", universalSelectedFile);
        fd.append("target_format", universalSelectedFormatTo);

        fetch(`${getApiBaseUrl()}/convert-universal`, {
            method: "POST",
            headers: {
                "X-Task-ID": taskId
            },
            body: fd
        })
            .then(async response => {
                if (!response.ok) {
                    const errData = await response.json().catch(() => ({}));
                    throw new Error(errData.message || "Dönüştürme işlemi başarısız oldu.");
                }
                return response.blob();
            })
            .then(blob => {
                const sourceName = universalSelectedFile.name.replace(/\.[^.]+$/, "");
                const outName = `${sourceName}.${universalSelectedFormatTo}`;
                downloadBlob(blob, outName);
                stopGlobalProgress(true, i18n('conversion_success'));
                showToast("success", `🎉 ${i18n('conversion_success')} — ${outName}`);
                resetUniversalConverter();
            })
            .catch(err => {
                stopGlobalProgress(false);
                showToast("error", `⚠️ ${err.message}`);

            });
    });

    // MAGIC ERASER
    const magicDropZone = document.getElementById("drop-zone-magic");
    const magicInput = document.getElementById("file-input-magic");
    const magicDropContainer = document.getElementById("magic-drop-container");
    const magicEditorContainer = document.getElementById("magic-editor-container");
    const magicCanvas = document.getElementById("magic-canvas");
    const magicBrushSlider = document.getElementById("magic-brush-slider");
    const magicBrushSizeVal = document.getElementById("magic-brush-size-val");
    const btnMagicClear = document.getElementById("btn-magic-clear-mask");
    const btnMagicClose = document.getElementById("btn-magic-close");
    const btnMagicApply = document.getElementById("btn-magic-apply");

    let magicOriginalFile = null;
    let magicCtx = null;
    let maskCanvas = null;
    let maskCtx = null;
    let isDrawing = false;
    let bgImageObj = null;

    if (magicDropZone) {
        setupDropZone(magicDropZone, magicInput, handleMagicFile);
    }

    function handleMagicFile(file) {
        if (!file.type.startsWith("image/")) {
            showToast("error", `⚠️ ${i18n('select_image_error')}`);
            return;
        }

        magicOriginalFile = file;
        const reader = new FileReader();
        reader.onload = (e) => {
            bgImageObj = new Image();
            bgImageObj.onload = () => {
                initMagicEditor();
            };
            bgImageObj.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }

    function initMagicEditor() {
        magicDropContainer.classList.add("hidden");
        magicEditorContainer.classList.remove("hidden");
        magicEditorContainer.classList.add("flex");

        magicCanvas.width = bgImageObj.width;
        magicCanvas.height = bgImageObj.height;

        maskCanvas = document.createElement("canvas");
        maskCanvas.width = bgImageObj.width;
        maskCanvas.height = bgImageObj.height;

        magicCtx = magicCanvas.getContext("2d");
        maskCtx = maskCanvas.getContext("2d");

        resetMagicMask();
    }

    function resetMagicMask() {
        if (!magicCtx || !maskCtx) return;

        magicCtx.clearRect(0, 0, magicCanvas.width, magicCanvas.height);
        magicCtx.drawImage(bgImageObj, 0, 0);

        maskCtx.fillStyle = "black";
        maskCtx.fillRect(0, 0, maskCanvas.width, maskCanvas.height);
    }

    function getMousePos(evt) {
        const rect = magicCanvas.getBoundingClientRect();
        const scaleX = magicCanvas.width / rect.width;
        const scaleY = magicCanvas.height / rect.height;

        // Touch events
        let clientX = evt.clientX;
        let clientY = evt.clientY;
        if (evt.touches && evt.touches.length > 0) {
            clientX = evt.touches[0].clientX;
            clientY = evt.touches[0].clientY;
        }

        return {
            x: (clientX - rect.left) * scaleX,
            y: (clientY - rect.top) * scaleY
        };
    }

    function startDrawing(e) {
        e.preventDefault();
        isDrawing = true;
        draw(e);
    }

    function stopDrawing() {
        isDrawing = false;
        magicCtx.beginPath();
        maskCtx.beginPath();
    }

    function draw(e) {
        if (!isDrawing) return;
        e.preventDefault();

        const pos = getMousePos(e);
        const brushSize = parseInt(magicBrushSlider.value);

        magicCtx.lineWidth = brushSize;
        magicCtx.lineCap = "round";
        magicCtx.lineJoin = "round";
        magicCtx.strokeStyle = "rgba(0, 255, 100, 0.4)";

        magicCtx.lineTo(pos.x, pos.y);
        magicCtx.stroke();
        magicCtx.beginPath();
        magicCtx.moveTo(pos.x, pos.y);

        maskCtx.lineWidth = brushSize;
        maskCtx.lineCap = "round";
        maskCtx.lineJoin = "round";
        maskCtx.strokeStyle = "white";

        maskCtx.lineTo(pos.x, pos.y);
        maskCtx.stroke();
        maskCtx.beginPath();
        maskCtx.moveTo(pos.x, pos.y);
    }

    if (magicCanvas) {
        magicCanvas.addEventListener("mousedown", startDrawing);
        magicCanvas.addEventListener("mousemove", draw);
        magicCanvas.addEventListener("mouseup", stopDrawing);
        magicCanvas.addEventListener("mouseleave", stopDrawing);

        // Touch support
        magicCanvas.addEventListener("touchstart", startDrawing, { passive: false });
        magicCanvas.addEventListener("touchmove", draw, { passive: false });
        magicCanvas.addEventListener("touchend", stopDrawing);
    }

    if (magicBrushSlider) {
        magicBrushSlider.addEventListener("input", (e) => {
            magicBrushSizeVal.textContent = e.target.value;
        });
    }

    if (btnMagicClear) {
        btnMagicClear.addEventListener("click", resetMagicMask);
    }

    if (btnMagicClose) {
        btnMagicClose.addEventListener("click", () => {
            magicOriginalFile = null;
            magicInput.value = "";
            magicEditorContainer.classList.add("hidden");
            magicEditorContainer.classList.remove("flex");
            magicDropContainer.classList.remove("hidden");
        });
    }

    if (btnMagicApply) {
        btnMagicApply.addEventListener("click", () => {
            if (!magicOriginalFile || !maskCanvas) return;

            btnMagicApply.disabled = true;
            btnMagicApply.querySelector('span').textContent = i18n('erasing_ai');
            btnMagicApply.querySelector('i').className = "fa-solid fa-circle-notch fa-spin text-white text-xl";

            const taskId = generateTaskId();
            startGlobalProgress(taskId);

            maskCanvas.toBlob((maskBlob) => {
                const fd = new FormData();
                fd.append("image", magicOriginalFile);
                fd.append("mask", maskBlob, "mask.png");

                fetch(`${getApiBaseUrl()}/magic-erase`, {
                    method: "POST",
                    headers: {
                        "X-Task-ID": taskId
                    },
                    body: fd
                })
                    .then(async response => {
                        if (!response.ok) {
                            const errData = await response.json().catch(() => ({}));
                            throw new Error(errData.message || "İşlem başarısız oldu.");
                        }
                        return response.blob();
                    })
                    .then(blob => {
                        const url = URL.createObjectURL(blob);

                        const resultObj = new Image();
                        resultObj.onload = () => {
                            magicCtx.clearRect(0, 0, magicCanvas.width, magicCanvas.height);
                            magicCtx.drawImage(resultObj, 0, 0);
                            bgImageObj = resultObj;

                            maskCtx.fillStyle = "black";
                            maskCtx.fillRect(0, 0, maskCanvas.width, maskCanvas.height);

                            const sourceName = magicOriginalFile.name.replace(/\.[^.]+$/, "");

                            // Convert Blob to File to allow further user edits
                            magicOriginalFile = new File([blob], `${sourceName}_erased.png`, { type: blob.type });

                            downloadBlob(blob, `${sourceName}_erased.png`);
                            stopGlobalProgress(true, i18n('completed'));
                            showToast("success", i18n('erase_success'));
                        };
                        resultObj.src = url;

                    })
                    .catch(err => {
                        stopGlobalProgress(false);
                        showToast("error", `⚠️ ${err.message}`);
                    })
                    .finally(() => {
                        btnMagicApply.disabled = false;
                        btnMagicApply.querySelector('span').textContent = i18n('magic_erase_btn');
                        btnMagicApply.querySelector('i').className = "fa-solid fa-wand-magic-sparkles text-xl group-hover:animate-pulse text-gold-light";
                    });
            }, "image/png");
        });
    }

    // IMAGE UPSCALER
    const dropUpscale = document.getElementById("drop-zone-upscale");
    const inputUpscale = document.getElementById("file-input-upscale");
    const infoUpscale = document.getElementById("info-upscale");
    const infoUpscaleName = document.getElementById("info-upscale-name");
    const infoUpscaleSize = document.getElementById("info-upscale-size");
    const upscalePanel = document.getElementById("upscale-panel");
    const upscaleProcessing = document.getElementById("upscale-processing");
    const btnUpscaleApply = document.getElementById("btn-upscale-apply");
    const upscaleOptions = document.querySelectorAll(".upscale-option-btn");

    let upscaleFile = null;
    let selectedScale = 2; // Default scale
    let selectedModel = "general"; // Default model

    if (dropUpscale) {
        setupDropZone(dropUpscale, inputUpscale, handleUpscaleFile, (e) => {
            if (e.target.closest("#upscale-panel")) return true; // Do not trigger file dialog when clicking inside panel
        });
    }

    function handleUpscaleFile(file) {
        if (!file.type.startsWith("image/")) {
            showToast("error", `⚠️ ${i18n('select_image_error')}`);
            return;
        }

        upscaleFile = file;

        infoUpscaleName.textContent = file.name;
        infoUpscaleSize.textContent = formatBytes(file.size);
        infoUpscale.classList.remove("hidden");
        infoUpscale.classList.add("visible");

        upscalePanel.classList.remove("hidden");
        upscalePanel.classList.add("flex");
        upscaleProcessing.classList.add("hidden");

        btnUpscaleApply.disabled = false;
        btnUpscaleApply.querySelector('span').textContent = i18n('btn_start_upscale');
        btnUpscaleApply.querySelector('i').className = "fa-solid fa-wand-magic-sparkles text-xl group-hover:animate-pulse text-gold-light";
    }

    upscaleOptions.forEach(btn => {
        btn.addEventListener("click", () => {
            upscaleOptions.forEach(b => {
                b.classList.remove("ring-2", "ring-purple-500", "bg-black/40");
                b.classList.add("border-white/5", "bg-white/5");
                const icon = b.querySelector("i");
                if (icon) {
                    icon.classList.remove("text-purple-400");
                    icon.classList.add("text-gray-500");
                }
            });

            btn.classList.add("ring-2", "ring-purple-500", "bg-black/40");
            btn.classList.remove("border-white/5", "bg-white/5");
            const btnIcon = btn.querySelector("i");
            if (btnIcon) {
                btnIcon.classList.add("text-purple-400");
                btnIcon.classList.remove("text-gray-500");
            }

            selectedScale = parseInt(btn.dataset.scale);
        });
    });

    const upscaleModelOptions = document.querySelectorAll(".upscale-model-btn");
    upscaleModelOptions.forEach(btn => {
        btn.addEventListener("click", () => {
            upscaleModelOptions.forEach(b => {
                b.classList.remove("ring-2", "ring-purple-500", "bg-black/40", "text-white");
                b.classList.add("border-white/5", "bg-white/5", "text-gray-300");
                const icon = b.querySelector("i");
                if (icon) {
                    icon.classList.remove("text-purple-400");
                    icon.classList.add("text-gray-500");
                }
            });

            btn.classList.add("ring-2", "ring-purple-500", "bg-black/40", "text-white");
            btn.classList.remove("border-white/5", "bg-white/5", "text-gray-300");
            const btnIcon = btn.querySelector("i");
            if (btnIcon) {
                btnIcon.classList.add("text-purple-400");
                btnIcon.classList.remove("text-gray-500");
            }

            selectedModel = btn.dataset.model || "general";
        });
    });

    if (btnUpscaleApply) {
        btnUpscaleApply.addEventListener("click", () => {
            if (!upscaleFile) return;

            btnUpscaleApply.disabled = true;
            btnUpscaleApply.querySelector('span').textContent = i18n('erasing_ai');
            btnUpscaleApply.querySelector('i').className = "fa-solid fa-circle-notch fa-spin text-white text-xl";

            const taskId = generateTaskId();
            startGlobalProgress(taskId);

            upscaleProcessing.classList.remove("hidden");

            const fd = new FormData();
            fd.append("file", upscaleFile);
            fd.append("scale", selectedScale);
            fd.append("model_type", selectedModel);

            fetch(`${getApiBaseUrl()}/upscale-image`, {
                method: "POST",
                headers: {
                    "X-Task-ID": taskId
                },
                body: fd
            })
                .then(async response => {
                    upscaleProcessing.classList.add("hidden");
                    if (!response.ok) {
                        const errData = await response.json().catch(() => ({}));
                        throw new Error(errData.message || "İşlem başarısız oldu.");
                    }
                    return response.blob();
                })
                .then(blob => {
                    const sourceName = upscaleFile.name.replace(/\.[^.]+$/, "");
                    const ext = upscaleFile.name.split('.').pop() || 'png';
                    const outName = `${sourceName}_upscaled_${selectedScale}x.${ext}`;
                    downloadBlob(blob, outName);
                    stopGlobalProgress(true, i18n('completed'));
                    showToast("success", `🎉 ${i18n('pixel_upscale_success')} — ${outName}`);

                    btnUpscaleApply.disabled = false;
                    btnUpscaleApply.querySelector('span').textContent = i18n('btn_start_upscale');
                    btnUpscaleApply.querySelector('i').className = "fa-solid fa-wand-magic-sparkles text-xl group-hover:animate-pulse text-gold-light";
                })
                .catch(err => {
                    stopGlobalProgress(false);
                    upscaleProcessing.classList.add("hidden");
                    showToast("error", `⚠️ ${err.message}`);

                    btnUpscaleApply.disabled = false;
                    btnUpscaleApply.querySelector('span').textContent = i18n('btn_start_upscale');
                    btnUpscaleApply.querySelector('i').className = "fa-solid fa-wand-magic-sparkles text-xl group-hover:animate-pulse text-gold-light";
                });
        });
    }

    // BACKGROUND REMOVER
    const dropBg = document.getElementById("drop-zone-bg");
    const inputBg = document.getElementById("file-input-bg");
    const progBg = document.getElementById("progress-bg");
    const barBg = document.getElementById("bar-bg");
    const infoBg = document.getElementById("info-bg");
    const infoBgName = document.getElementById("info-bg-name");
    const infoBgSize = document.getElementById("info-bg-size");
    const bgPanel = document.getElementById("bg-panel");
    const previewOrig = document.getElementById("bg-preview-original");
    const previewResult = document.getElementById("bg-preview-result");
    const resultPlaceh = document.getElementById("bg-result-placeholder");
    const aiProcessing = document.getElementById("ai-processing");
    const btnRemoveBg = document.getElementById("btn-remove-bg");

    let bgFile = null;

    setupDropZone(dropBg, inputBg, handleBgFile, (e) => {
        if (e.target.closest("#bg-panel")) return true;
    });

    function handleBgFile(file) {
        if (!file.type.startsWith("image/")) {
            showToast("error", `⚠️ ${i18n('select_image_error')}`);
            return;
        }

        bgFile = file;

        infoBgName.textContent = file.name;
        infoBgSize.textContent = formatBytes(file.size);
        infoBg.classList.add("visible");

        const reader = new FileReader();
        reader.onload = (e) => {
            previewOrig.src = e.target.result;
        };
        reader.readAsDataURL(file);

        bgPanel.classList.remove("hidden");
        previewResult.classList.add("hidden");
        previewResult.src = "";
        resultPlaceh.classList.remove("hidden");
        aiProcessing.classList.add("hidden");
        btnRemoveBg.disabled = false;
        btnRemoveBg.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i><span>${i18n('btn_remove_bg')}</span>`;
    }

    btnRemoveBg.addEventListener("click", (e) => {
        e.stopPropagation();
        if (!bgFile) return;
        removeBgRequest(bgFile);
    });

    function removeBgRequest(file) {
        const taskId = generateTaskId();
        startGlobalProgress(taskId);

        const fd = new FormData();
        fd.append("file", file);
        const xhr = new XMLHttpRequest();

        progBg.classList.add("visible");
        barBg.style.width = "0%";
        btnRemoveBg.disabled = true;
        btnRemoveBg.innerHTML = `<div class="spinner visible" style="width:18px;height:18px;border-width:2px;display:inline-block"></div><span>Processing...</span>`;

        aiProcessing.classList.remove("hidden");

        xhr.responseType = "blob";

        xhr.upload.addEventListener("progress", (e) => {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 100);
                barBg.style.width = percent + "%";
                document.getElementById("percent-bg").textContent = percent + "%";
            }
        });

        xhr.addEventListener("load", () => {
            barBg.style.width = "100%";
            aiProcessing.classList.add("hidden");

            if (xhr.status === 200) {
                const blob = xhr.response;
                // Revoke previous blob URL to prevent memory leaks
                if (previewResult.src && previewResult.src.startsWith("blob:")) {
                    URL.revokeObjectURL(previewResult.src);
                }
                const url = URL.createObjectURL(blob);
                previewResult.src = url;
                previewResult.classList.remove("hidden");
                resultPlaceh.classList.add("hidden");

                const stem = file.name.replace(/\.[^.]+$/, "");
                downloadBlob(blob, `${stem}_nobg.png`);

                stopGlobalProgress(true, "Arka Plan Başarıyla Kaldırıldı!");
                showToast("success", `🪄 İşlem Başarılı! Arka plan kaldırıldı.`);
            } else {
                stopGlobalProgress(false);
                readBlobError(xhr.response);
            }
            setTimeout(() => {
                progBg.classList.remove("visible");
                barBg.style.width = "0%";
                document.getElementById("percent-bg").textContent = "0%";
                btnRemoveBg.disabled = false;
                btnRemoveBg.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i><span>Sihirli Arka Planı Kaldır</span>`;
            }, 1500);
        });

        xhr.addEventListener("error", () => {
            stopGlobalProgress(false);
            aiProcessing.classList.add("hidden");
            showToast("error", "⚠️ Sunucu bağlantı hatası.");
            btnRemoveBg.disabled = false;
            btnRemoveBg.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i><span>Sihirli Arka Planı Kaldır</span>`;
        });

        xhr.open("POST", `${getApiBaseUrl()}/remove-background`);
        xhr.setRequestHeader("X-Task-ID", taskId);
        xhr.send(fd);
    }

    const videoUrlInput = document.getElementById("video-url-input");
    const btnFetchInfo = document.getElementById("btn-fetch-info");
    const fetchLoading = document.getElementById("video-fetch-loading");
    const videoInfoPanel = document.getElementById("video-info-panel");
    const videoThumbnail = document.getElementById("video-thumbnail");
    const videoDuration = document.getElementById("video-duration");
    const videoTitle = document.getElementById("video-title");
    const videoUploader = document.getElementById("video-uploader");
    const videoFormatChips = document.getElementById("video-format-chips");
    const btnDownloadVideo = document.getElementById("btn-download-video");
    const downloadLoading = document.getElementById("video-download-loading");

    let currentVideoUrl = "";
    let selectedVideoFormat = "best";

    function _resolutionIcon(h) {
        if (h >= 2160) return "fa-crown";
        if (h >= 1440) return "fa-star";
        if (h >= 1080) return "fa-circle-play";
        if (h >= 720) return "fa-film";
        return "fa-compact-disc";
    }

    function _resolutionLabel(h) {
        if (h >= 2160) return `${h}p (4K)`;
        if (h >= 1440) return `${h}p (2K)`;
        if (h >= 1080) return `${h}p (Full HD)`;
        if (h >= 720) return `${h}p (HD)`;
        return `${h}p`;
    }

    function buildVideoFormatChips(resolutions) {
        videoFormatChips.innerHTML = "";

        const filtered = resolutions.filter(h => h >= 240);

        const bestChip = document.createElement("button");
        bestChip.className = "format-chip selected";
        bestChip.dataset.format = "best";
        bestChip.innerHTML = `<i class="fa-solid fa-crown"></i><span>${i18n('best_quality')}</span>`;
        bestChip.addEventListener("click", () => {
            videoFormatChips.querySelectorAll(".format-chip").forEach(c => c.classList.remove("selected"));
            bestChip.classList.add("selected");
            selectedVideoFormat = "best";
        });
        videoFormatChips.appendChild(bestChip);

        filtered.forEach((h) => {
            const chip = document.createElement("button");
            chip.className = "format-chip";
            chip.dataset.format = String(h);
            chip.innerHTML = `<i class="fa-solid ${_resolutionIcon(h)}"></i><span>${_resolutionLabel(h)}</span>`;
            chip.addEventListener("click", () => {
                videoFormatChips.querySelectorAll(".format-chip").forEach(c => c.classList.remove("selected"));
                chip.classList.add("selected");
                selectedVideoFormat = String(h);
            });
            videoFormatChips.appendChild(chip);
        });

        const mp3Chip = document.createElement("button");
        mp3Chip.className = "format-chip";
        mp3Chip.dataset.format = "mp3";
        mp3Chip.innerHTML = `<i class="fa-solid fa-music"></i><span>${i18n('only_audio')}</span>`;
        mp3Chip.addEventListener("click", () => {
            videoFormatChips.querySelectorAll(".format-chip").forEach(c => c.classList.remove("selected"));
            mp3Chip.classList.add("selected");
            selectedVideoFormat = "mp3";
        });
        videoFormatChips.appendChild(mp3Chip);

        selectedVideoFormat = "best";
    }

    videoUrlInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            btnFetchInfo.click();
        }
    });

    btnFetchInfo.addEventListener("click", async () => {
        const url = videoUrlInput.value.trim();
        if (!url) {
            showToast("error", `⚠️ ${i18n('url_error')}`);
            return;
        }

        btnFetchInfo.disabled = true;
        fetchLoading.classList.remove("hidden");
        videoInfoPanel.classList.add("hidden");
        spinner.classList.add("visible");

        try {
            const res = await fetch(`${getApiBaseUrl()}/fetch-video-info`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url }),
            });

            const data = await res.json();

            if (!data.success) {
                showToast("error", `⚠️ ${data.message}`);
                return;
            }

            currentVideoUrl = url;
            videoThumbnail.src = data.thumbnail || "";
            videoDuration.textContent = data.duration || "";
            videoTitle.textContent = data.title || i18n('unknown');
            videoUploader.textContent = data.uploader ? `📺 ${data.uploader}` : "";

            const resolutions = data.resolutions || [];
            buildVideoFormatChips(resolutions);

            videoInfoPanel.classList.remove("hidden");
            showToast("success", `✅ ${i18n('fetch_success')}`);

        } catch (err) {
            showToast("error", `⚠️ ${i18n('server_error')}`);
        } finally {
            btnFetchInfo.disabled = false;
            fetchLoading.classList.add("hidden");
            spinner.classList.remove("visible");
        }
    });

    btnDownloadVideo.addEventListener("click", async () => {
        if (!currentVideoUrl) {
            showToast("error", "⚠️ Önce video bilgilerini getirin.");
            return;
        }

        btnDownloadVideo.disabled = true;
        btnDownloadVideo.innerHTML = `<div class="spinner visible" style="width:18px;height:18px;border-width:2px;display:inline-block"></div><span>Başlatılıyor…</span>`;
        downloadLoading.classList.remove("hidden");
        spinner.classList.add("visible");

        try {
            const startRes = await fetch(`${getApiBaseUrl()}/start-download`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    url: currentVideoUrl,
                    format_id: selectedVideoFormat,
                    title: videoTitle.textContent || "video"
                }),
            });

            const startData = await startRes.json();
            if (!startData.success) {
                showToast("error", `⚠️ ${startData.message || "İndirme başlatılamadı."}`);
                resetVideoUI();
                return;
            }

            const taskId = startData.task_id;
            btnDownloadVideo.innerHTML = `<div class="spinner visible" style="width:18px;height:18px;border-width:2px;display:inline-block"></div><span>İndiriliyor… %0</span>`;

            const downloadResult = await pollDownloadStatus(taskId);

            if (downloadResult.status === "done") {
                btnDownloadVideo.innerHTML = `<div class="spinner visible" style="width:18px;height:18px;border-width:2px;display:inline-block"></div><span>Farklı Kaydet açılıyor…</span>`;

                let savedViaNative = false;
                if (currentMode === 'pc' || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
                    try {
                        const saveRes = await fetch(`${getApiBaseUrl()}/api/save-task-file`, {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({
                                task_id: taskId,
                                suggested_name: downloadResult.filename || "video.mp4"
                            })
                        });
                        if (saveRes.ok) {
                            const saveJson = await saveRes.json();
                            if (saveJson.success && saveJson.saved_path) {
                                savedViaNative = true;
                                showToast("success", `🎉 Video başarıyla kaydedildi:\n${saveJson.saved_path}`);
                            } else if (saveJson.canceled) {
                                savedViaNative = true;
                                showToast("info", "Video kaydetme işlemi kullanıcı tarafından iptal edildi.");
                            }
                        }
                    } catch (e) {
                        console.warn("Native save dialog fallback:", e);
                    }
                }

                if (!savedViaNative) {
                    const a = document.createElement("a");
                    a.href = `${getApiBaseUrl()}/download-file/${taskId}`;
                    a.download = downloadResult.filename || "video.mp4";
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    showToast("success", `🎉 İndirme Başarılı! — ${downloadResult.filename}`);
                }
            } else {
                showToast("error", `⚠️ ${downloadResult.error || "İndirme başarısız."}`);
            }

        } catch (err) {
            showToast("error", "⚠️ Sunucu bağlantı hatası.");
        } finally {
            resetVideoUI();
        }
    });

    async function pollDownloadStatus(taskId) {
        const loadingText = downloadLoading.querySelector("p.text-sm");

        while (true) {
            await new Promise(r => setTimeout(r, 800));

            try {
                const res = await fetch(`${getApiBaseUrl()}/download-status/${taskId}`);
                const data = await res.json();

                if (!data.success) {
                    return { status: "error", error: data.message };
                }

                const pct = data.progress || 0;
                const speedInfo = data.speed ? ` · ${data.speed}` : "";

                btnDownloadVideo.innerHTML = `<div class="spinner visible" style="width:18px;height:18px;border-width:2px;display:inline-block"></div><span>İndiriliyor… %${pct}${speedInfo}</span>`;

                if (loadingText) {
                    if (pct >= 97) {
                        loadingText.textContent = "Birleştirme ve dönüştürme yapılıyor…";
                    } else {
                        loadingText.textContent = `Video İndiriliyor… %${pct}${speedInfo}`;
                    }
                }

                if (data.status === "done") {
                    return { status: "done", filename: data.filename };
                } else if (data.status === "error") {
                    return { status: "error", error: data.error };
                }

            } catch (e) {
                return { status: "error", error: "Sunucu bağlantısı kesildi." };
            }
        }
    }

    function resetVideoUI() {
        btnDownloadVideo.disabled = false;
        btnDownloadVideo.innerHTML = `<i class="fa-solid fa-download"></i><span>${i18n('btn_start_download')}</span>`;
        downloadLoading.classList.add("hidden");
        spinner.classList.remove("visible");
    }

    const dropVault = document.getElementById("drop-zone-vault");
    const inputVaultMulti = document.getElementById("file-input-vault-multi");
    const inputVaultDir = document.getElementById("file-input-vault-dir");
    const btnModeFile = document.getElementById("vault-mode-file");
    const btnModeDir = document.getElementById("vault-mode-dir");
    const vaultDropTitle = document.getElementById("vault-drop-title");
    const vaultIcon = document.getElementById("vault-icon");
    const vaultDropHint = document.getElementById("vault-drop-hint");

    const infoVault = document.getElementById("info-vault");
    const infoVaultName = document.getElementById("info-vault-name");
    const infoVaultSize = document.getElementById("info-vault-size");
    const btnVaultClear = document.getElementById("btn-vault-clear");
    const vaultPanel = document.getElementById("vault-panel");

    const vaultPassword = document.getElementById("vault-password");
    const btnVaultEncrypt = document.getElementById("btn-vault-encrypt");
    const btnVaultDecrypt = document.getElementById("btn-vault-decrypt");

    let vaultFiles = [];
    let vaultMode = "file"; // 'file' or 'dir'

    function updateVaultModeUI() {
        if (vaultMode === "file") {
            btnModeFile.className = "px-6 py-3 rounded-xl font-bold text-white bg-black/40 ring-2 ring-purple-500 transition-all flex items-center gap-2 shadow-[0_0_15px_rgba(168,85,247,0.3)]";
            btnModeDir.className = "px-6 py-3 rounded-xl font-bold text-gray-300 bg-white/5 hover:bg-white/10 transition-all flex items-center gap-2 border border-white/10";
            vaultDropTitle.textContent = i18n('vault_drop_text');
            vaultIcon.innerHTML = `<i class="fa-solid fa-file-shield"></i>`;
            if (vaultDropHint) vaultDropHint.innerHTML = i18n('vault_drop_click');

            if (btnVaultDecrypt) btnVaultDecrypt.classList.remove("hidden");
            if (btnVaultEncrypt) {
                btnVaultEncrypt.classList.remove("hidden");
                btnVaultEncrypt.innerHTML = `<i class="fa-solid fa-lock"></i> ${i18n('btn_vault_encrypt')}`;
            }
        } else {
            btnModeDir.className = "px-6 py-3 rounded-xl font-bold text-white bg-black/40 ring-2 ring-purple-500 transition-all flex items-center gap-2 shadow-[0_0_15px_rgba(168,85,247,0.3)]";
            btnModeFile.className = "px-6 py-3 rounded-xl font-bold text-gray-300 bg-white/5 hover:bg-white/10 transition-all flex items-center gap-2 border border-white/10";
            vaultDropTitle.textContent = i18n('vault_drop_folder_title');
            vaultIcon.innerHTML = `<i class="fa-solid fa-folder-closed"></i>`;
            if (vaultDropHint) vaultDropHint.innerHTML = i18n('vault_drop_hint_folder');

            if (btnVaultDecrypt) btnVaultDecrypt.classList.add("hidden");
            if (btnVaultEncrypt) {
                btnVaultEncrypt.classList.remove("hidden");
                btnVaultEncrypt.innerHTML = `<i class="fa-solid fa-folder-tree"></i> ${i18n('vault_encrypt_folder_btn')}`;
            }
        }
    }

    if (btnModeFile) {
        btnModeFile.addEventListener("click", () => {
            vaultMode = "file";
            updateVaultModeUI();
        });
    }

    if (btnModeDir) {
        btnModeDir.addEventListener("click", () => {
            vaultMode = "dir";
            updateVaultModeUI();
        });
    }

    function addVaultFiles(fileList) {
        if (!fileList || fileList.length === 0) return;
        for (let i = 0; i < fileList.length; i++) {
            // Ignorating empty files/folders in directory drop if needed
            vaultFiles.push(fileList[i]);
        }
        updateVaultUI();
    }

    function updateVaultUI() {
        if (vaultFiles.length === 0) {
            infoVault.classList.remove("visible");
            infoVault.classList.add("hidden");
            vaultPanel.classList.remove("flex");
            vaultPanel.classList.add("hidden");
            vaultPassword.value = "";
            return;
        }

        if (vaultFiles.length === 1) {
            infoVaultName.textContent = vaultFiles[0].name;
            infoVaultSize.textContent = formatBytes(vaultFiles[0].size);
        } else {
            const totalSize = vaultFiles.reduce((acc, f) => acc + f.size, 0);
            infoVaultName.textContent = `${vaultFiles.length} ${i18n('folder_selected')}`;
            infoVaultSize.textContent = `${i18n('total_size')} ${formatBytes(totalSize)}`;
        }

        infoVault.classList.remove("hidden");
        infoVault.classList.add("visible");

        vaultPanel.classList.remove("hidden");
        vaultPanel.classList.add("flex");
    }

    if (inputVaultMulti) {
        inputVaultMulti.addEventListener("change", (e) => { addVaultFiles(e.target.files); });
    }
    if (inputVaultDir) {
        inputVaultDir.addEventListener("change", (e) => { addVaultFiles(e.target.files); });
    }

    if (dropVault) {
        dropVault.addEventListener("click", (e) => {
            if (e.target.closest("#btn-vault-clear") || e.target.closest("#info-vault") || e.target.tagName.toLowerCase() === 'input') {
                return;
            }

            if (vaultMode === "file") {
                inputVaultMulti.click();
            } else {
                inputVaultDir.click();
            }
        });

        dropVault.addEventListener("dragover", (e) => {
            e.preventDefault();
            dropVault.classList.add("drag-over");
        });
        dropVault.addEventListener("dragleave", (e) => {
            e.preventDefault();
            dropVault.classList.remove("drag-over");
        });
        dropVault.addEventListener("drop", (e) => {
            e.preventDefault();
            dropVault.classList.remove("drag-over");
            if (e.target.closest("#btn-vault-clear") || e.target.closest("#info-vault")) return;

            if (e.dataTransfer && e.dataTransfer.files) {
                // Drop is handled uniformly, whether it's file or dir
                addVaultFiles(e.dataTransfer.files);
            }
        });
    }

    if (btnVaultClear) {
        btnVaultClear.addEventListener("click", (e) => {
            e.stopPropagation(); // prevent opening file chooser
            vaultFiles = [];
            if (inputVaultMulti) inputVaultMulti.value = "";
            if (inputVaultDir) inputVaultDir.value = "";
            updateVaultUI();
        });
    }

    function processVaultRequest(endpoint) {
        if (vaultFiles.length === 0) return;
        const pwd = vaultPassword.value.trim();
        if (!pwd) {
            showToast("error", `⚠️ ${i18n('enter_password')}`);
            return;
        }

        const isEncrypt = endpoint === "/encrypt-file";
        const btn = isEncrypt ? btnVaultEncrypt : btnVaultDecrypt;
        const originalContent = btn.innerHTML;

        btn.disabled = true;
        btn.innerHTML = `<div class="spinner visible" style="width:18px;height:18px;border-width:2px;display:inline-block"></div><span>İşleniyor…</span>`;

        const taskId = generateTaskId();
        startGlobalProgress(taskId);
        if (globalProgressMessage) {
            globalProgressMessage.textContent = i18n('encrypting_data');
        }

        const fd = new FormData();
        if (isEncrypt) {
            vaultFiles.forEach((f) => {
                const path = f.webkitRelativePath || f.name;
                fd.append("files", f, path);
            });
        } else {
            fd.append("file", vaultFiles[0], vaultFiles[0].name);
        }
        fd.append("password", pwd);

        fetch(`${getApiBaseUrl()}${endpoint}`, {
            method: "POST",
            headers: {
                "X-Task-ID": taskId
            },
            body: fd
        })
            .then(async response => {
                if (!response.ok) {
                    if (response.status === 400 && !isEncrypt) {
                        throw new Error(i18n('wrong_password'));
                    }
                    const errData = await response.json().catch(() => ({}));
                    throw new Error(errData.detail || errData.message || "İşlem başarısız oldu.");
                }
                return response.blob();
            })
            .then(blob => {
                let outName = "";
                if (isEncrypt) {
                    if (vaultFiles.length === 1 && vaultMode === "file") {
                        outName = `${vaultFiles[0].name}.enc`;
                    } else {
                        outName = "kasa_arsivi.zip.enc";
                    }
                } else {
                    outName = vaultFiles[0].name;
                    if (outName.endsWith(".enc")) {
                        outName = outName.slice(0, -4);
                    } else {
                        outName = `decrypted_${outName}`;
                    }
                }

                downloadBlob(blob, outName);
                stopGlobalProgress(true, isEncrypt ? i18n('encrypt_success') : i18n('decrypt_success'));
                showToast("success", `🎉 ${i18n('completed')} — ${outName}`);

                if (btnVaultClear) {
                    btnVaultClear.click();
                }
            })
            .catch(err => {
                stopGlobalProgress(false);
                showToast("error", `⚠️ Hata: ${err.message}`);
            })
            .finally(() => {
                btn.disabled = false;
                btn.innerHTML = originalContent;
            });
    }

    if (btnVaultEncrypt) {
        btnVaultEncrypt.addEventListener("click", () => processVaultRequest("/encrypt-file"));
    }

    if (btnVaultDecrypt) {
        btnVaultDecrypt.addEventListener("click", () => processVaultRequest("/decrypt-file"));
    }

    // ═══════════════════════════════════════════════════════════
    //  ORTAK FONKSİYONLAR
    // ═══════════════════════════════════════════════════════════

    /**
     * @param {HTMLElement} zone 
     * @param {HTMLInputElement} input 
     * @param {Function} onFile 
     * @param {Function} [clickGuard]
     */
    function setupDropZone(zone, input, onFile, clickGuard) {
        zone.addEventListener("click", (e) => {
            if (e.target === input || e.target.tagName.toLowerCase() === 'input') return;
            if (clickGuard && clickGuard(e)) return;
            input.click();
        });

        ["dragenter", "dragover"].forEach((evt) =>
            zone.addEventListener(evt, (e) => { e.preventDefault(); zone.classList.add("drag-over"); })
        );
        ["dragleave", "drop"].forEach((evt) =>
            zone.addEventListener(evt, (e) => { e.preventDefault(); zone.classList.remove("drag-over"); })
        );

        zone.addEventListener("drop", (e) => {
            if (e.dataTransfer.files.length > 0) onFile(e.dataTransfer.files[0]);
        });
        input.addEventListener("change", () => {
            if (input.files.length > 0) onFile(input.files[0]);
        });
    }

    async function downloadBlob(blob, filename) {
        // 1. Yerel PC modunda (Masaüstü uygulaması veya yerel sunucu)
        // Kullanıcıya Windows'un gerçek "Farklı Kaydet" penceresini açtır
        if (currentMode === 'pc' || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            try {
                const fd = new FormData();
                fd.append("file", blob, filename);
                fd.append("suggested_filename", filename);

                const res = await fetch(`${getApiBaseUrl()}/api/save-blob-file`, {
                    method: "POST",
                    body: fd
                });
                if (res.ok) {
                    const data = await res.json();
                    if (data.success && data.saved_path) {
                        showToast("success", `💾 Dosya kaydedildi: ${data.saved_path}`);
                        return;
                    } else if (data.canceled) {
                        showToast("info", "Kaydetme işlemi iptal edildi.");
                        return;
                    }
                }
            } catch (err) {
                console.warn("Native save dialog fallback:", err);
            }
        }

        // 2. Modern Tarayıcı "Farklı Kaydet" Penceresi (File System Access API)
        if (window.showSaveFilePicker) {
            try {
                const ext = filename.split('.').pop() || '';
                const mimeType = blob.type || 'application/octet-stream';
                const handle = await window.showSaveFilePicker({
                    suggestedName: filename,
                    types: [{
                        description: `${ext.toUpperCase()} Dosyası`,
                        accept: { [mimeType]: [`.${ext}`] }
                    }]
                });
                const writable = await handle.createWritable();
                await writable.write(blob);
                await writable.close();
                showToast("success", `💾 Dosya kaydedildi: ${handle.name}`);
                return;
            } catch (err) {
                if (err.name === 'AbortError') {
                    showToast("info", "Kaydetme iptal edildi.");
                    return;
                }
            }
        }

        // 3. Klasik Tarayıcı İndirme Bağlantısı Fallback
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
    }

    function readBlobError(blob) {
        const reader = new FileReader();
        reader.onload = () => {
            try {
                const err = JSON.parse(reader.result);
                showToast("error", `⚠️ ${err.message || i18n('vault_action_failed')}`);
            } catch {
                showToast("error", `⚠️ ${i18n('vault_action_failed')}`);
            }
        };
        reader.readAsText(blob);
    }

    window.showToast = function (type, message, title = "") {
        const toast = document.createElement("div");
        toast.className = `toast toast-${type}`;

        const typeIcons = {
            success: "fa-circle-check",
            error: "fa-circle-xmark",
            info: "fa-circle-info",
            warning: "fa-triangle-exclamation"
        };

        const typeTitles = {
            success: i18n('toast_success'),
            error: i18n('toast_error'),
            info: i18n('toast_info'),
            warning: i18n('toast_info')
        };

        const displayTitle = title || typeTitles[type];

        toast.innerHTML = `
            <i class="fa-solid ${typeIcons[type]} text-xl"></i>
            <div class="flex-1">
                <p class="font-bold text-sm text-white">${displayTitle}</p>
                <p class="text-xs text-gray-400 mt-0.5">${message}</p>
            </div>
        `;
        toastContainer.appendChild(toast);
        setTimeout(() => {
            toast.classList.add("removing");
            toast.addEventListener("animationend", () => toast.remove());
        }, 4000);
    }

    function formatBytes(bytes) {
        if (bytes === 0) return "0 B";
        const k = 1024;
        const units = ["B", "KB", "MB", "GB"];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + units[i];
    }

    const btnSyncUpdate = document.getElementById("btn-sync-update");
    const updateModal = document.getElementById("update-modal");

    if (btnSyncUpdate) {
        btnSyncUpdate.addEventListener("click", async () => {
            const taskId = generateTaskId();

            btnSyncUpdate.disabled = true;
            btnSyncUpdate.classList.add("opacity-50");

            startGlobalProgress(taskId);

            try {
                const response = await fetch("/apply-update", {
                    method: "POST",
                    headers: {
                        "X-Task-ID": taskId
                    }
                });

                const data = await response.json();

                stopGlobalProgress(response.ok, response.ok ? "Success" : "Error");

                if (response.ok) {
                    updateModal.classList.remove("hidden");
                } else {
                    showToast("error", `⚠️ ${data.message || 'Update failed'}`);
                }
            } catch (err) {
                stopGlobalProgress(false);
                showToast("error", `⚠️ Connection error: ${err.message}`);
            } finally {
                btnSyncUpdate.disabled = false;
                btnSyncUpdate.classList.remove("opacity-50");
            }
        });
    }

    // ═════════════════════════════════════════════════════════════
    // 1. VOCAL SEPARATOR (DEMUCS)
    // ═════════════════════════════════════════════════════════════
    let separatorFile = null;
    let selectedStems = "vocals";
    const dropSep = document.getElementById("drop-zone-separator");
    const inputSep = document.getElementById("file-input-separator");
    const infoSep = document.getElementById("info-separator");
    const nameSep = document.getElementById("info-separator-name");
    const sizeSep = document.getElementById("info-separator-size");
    const btnSepClear = document.getElementById("btn-separator-clear");
    const btnSepApply = document.getElementById("btn-separator-apply");
    const stemBtns = document.querySelectorAll(".separator-stem-btn");

    if (dropSep && inputSep) {
        dropSep.addEventListener("click", (e) => {
            if (e.target !== btnSepClear && !btnSepClear.contains(e.target)) {
                inputSep.click();
            }
        });

        inputSep.addEventListener("change", (e) => {
            if (e.target.files.length) {
                separatorFile = e.target.files[0];
                nameSep.textContent = separatorFile.name;
                sizeSep.textContent = formatBytes(separatorFile.size);
                infoSep.classList.remove("hidden");
            }
        });

        btnSepClear.addEventListener("click", (e) => {
            e.stopPropagation();
            separatorFile = null;
            inputSep.value = "";
            infoSep.classList.add("hidden");
        });

        stemBtns.forEach(btn => {
            btn.addEventListener("click", () => {
                stemBtns.forEach(b => {
                    b.className = "separator-stem-btn py-3 px-4 rounded-xl border border-white/10 bg-white/5 text-gray-300 font-semibold text-sm hover:border-white/20";
                });
                btn.className = "separator-stem-btn py-3 px-4 rounded-xl border border-rose-500 bg-rose-500/20 text-white font-bold text-sm";
                selectedStems = btn.dataset.stems;
            });
        });

        btnSepApply.addEventListener("click", async () => {
            if (!separatorFile) {
                showToast("error", i18n("select_audio_video_error"));
                return;
            }

            const taskId = generateTaskId();
            btnSepApply.disabled = true;
            startGlobalProgress(taskId);

            const fd = new FormData();
            fd.append("file", separatorFile);
            fd.append("stems", selectedStems);

            try {
                const apiBase = getApiBaseUrl();
                const resp = await fetch(`${apiBase}/separate-audio`, {
                    method: "POST",
                    headers: { "X-Task-ID": taskId },
                    body: fd
                });
                if (!resp.ok) {
                    const err = await resp.json().catch(() => ({}));
                    throw new Error(err.message || "Ayrıştırma başarısız oldu.");
                }
                const blob = await resp.blob();
                const outName = `${separatorFile.name.replace(/\.[^.]+$/, "")}_stems.zip`;
                downloadBlob(blob, outName);
                stopGlobalProgress(true, "Ayrıştırma Tamamlandı!");
                showToast("success", `🎵 Ayrıştırılmış parçalar indirildi: ${outName}`);
            } catch (err) {
                stopGlobalProgress(false);
                showToast("error", `⚠️ ${err.message}`);
            } finally {
                btnSepApply.disabled = false;
            }
        });
    }

    // ═════════════════════════════════════════════════════════════
    // 2. AI TRANSCRIBER (FASTER-WHISPER)
    // ═════════════════════════════════════════════════════════════
    let transcriberFile = null;
    const dropTrans = document.getElementById("drop-zone-transcriber");
    const inputTrans = document.getElementById("file-input-transcriber");
    const infoTrans = document.getElementById("info-transcriber");
    const nameTrans = document.getElementById("info-transcriber-name");
    const sizeTrans = document.getElementById("info-transcriber-size");
    const btnTransClear = document.getElementById("btn-transcriber-clear");
    const btnTransApply = document.getElementById("btn-transcriber-apply");
    const transFormat = document.getElementById("transcriber-format");
    const transLang = document.getElementById("transcriber-lang");
    const transResultBox = document.getElementById("transcription-result-box");
    const transPreview = document.getElementById("transcription-text-preview");
    const btnCopyTrans = document.getElementById("btn-copy-transcript");

    if (dropTrans && inputTrans) {
        dropTrans.addEventListener("click", (e) => {
            if (e.target !== btnTransClear && !btnTransClear.contains(e.target)) {
                inputTrans.click();
            }
        });

        inputTrans.addEventListener("change", (e) => {
            if (e.target.files.length) {
                transcriberFile = e.target.files[0];
                nameTrans.textContent = transcriberFile.name;
                sizeTrans.textContent = formatBytes(transcriberFile.size);
                infoTrans.classList.remove("hidden");
            }
        });

        btnTransClear.addEventListener("click", (e) => {
            e.stopPropagation();
            transcriberFile = null;
            inputTrans.value = "";
            infoTrans.classList.add("hidden");
            transResultBox.classList.add("hidden");
        });

        if (btnCopyTrans) {
            btnCopyTrans.addEventListener("click", () => {
                if (transPreview.value) {
                    navigator.clipboard.writeText(transPreview.value);
                    showToast("info", "📋 " + i18n("copied_to_clipboard"));
                }
            });
        }

        btnTransApply.addEventListener("click", async () => {
            if (!transcriberFile) {
                showToast("error", i18n("select_audio_video_error"));
                return;
            }

            const taskId = generateTaskId();
            btnTransApply.disabled = true;
            startGlobalProgress(taskId);

            const fd = new FormData();
            fd.append("file", transcriberFile);
            fd.append("output_format", transFormat ? transFormat.value : "txt");
            fd.append("language", transLang ? transLang.value : "auto");
            fd.append("model_size", "base");

            try {
                const apiBase = getApiBaseUrl();
                const resp = await fetch(`${apiBase}/transcribe-media`, {
                    method: "POST",
                    headers: { "X-Task-ID": taskId },
                    body: fd
                });
                if (!resp.ok) {
                    const err = await resp.json().catch(() => ({}));
                    throw new Error(err.message || "Transkripsiyon başarısız oldu.");
                }

                const contentType = resp.headers.get("content-type") || "";
                if (contentType.includes("application/json")) {
                    const data = await resp.json();
                    transPreview.value = data.full_text || JSON.stringify(data, null, 2);
                    transResultBox.classList.remove("hidden");
                } else {
                    const blob = await resp.blob();
                    const text = await blob.text();
                    transPreview.value = text.substring(0, 1500) + (text.length > 1500 ? "\n... (tamamı indirildi)" : "");
                    transResultBox.classList.remove("hidden");
                    const ext = transFormat.value === "srt" ? "srt" : "txt";
                    downloadBlob(blob, `${transcriberFile.name.replace(/\.[^.]+$/, "")}_transcript.${ext}`);
                }

                stopGlobalProgress(true, "Transkripsiyon Tamamlandı!");
                showToast("success", "🎙️ Transkript başarıyla oluşturuldu.");
            } catch (err) {
                stopGlobalProgress(false);
                showToast("error", `⚠️ ${err.message}`);
            } finally {
                btnTransApply.disabled = false;
            }
        });
    }

    // ═════════════════════════════════════════════════════════════
    // 3. EXIF & PRIVACY METADATA CLEANER
    // ═════════════════════════════════════════════════════════════
    let metaFile = null;
    const dropMeta = document.getElementById("drop-zone-metadata");
    const inputMeta = document.getElementById("file-input-metadata");
    const infoMeta = document.getElementById("info-metadata");
    const nameMeta = document.getElementById("info-metadata-name");
    const sizeMeta = document.getElementById("info-metadata-size");
    const btnMetaClear = document.getElementById("btn-metadata-clear");
    const btnMetaInspect = document.getElementById("btn-metadata-inspect");
    const btnMetaStrip = document.getElementById("btn-metadata-strip");
    const metaReportBox = document.getElementById("metadata-report-box");
    const metaTagsList = document.getElementById("metadata-tags-list");

    if (dropMeta && inputMeta) {
        dropMeta.addEventListener("click", (e) => {
            if (e.target !== btnMetaClear && !btnMetaClear.contains(e.target)) {
                inputMeta.click();
            }
        });

        inputMeta.addEventListener("change", (e) => {
            if (e.target.files.length) {
                metaFile = e.target.files[0];
                nameMeta.textContent = metaFile.name;
                sizeMeta.textContent = formatBytes(metaFile.size);
                infoMeta.classList.remove("hidden");
            }
        });

        btnMetaClear.addEventListener("click", (e) => {
            e.stopPropagation();
            metaFile = null;
            inputMeta.value = "";
            infoMeta.classList.add("hidden");
            metaReportBox.classList.add("hidden");
        });

        btnMetaInspect.addEventListener("click", async () => {
            if (!metaFile) {
                showToast("error", i18n("select_inspect_img_error"));
                return;
            }
            const fd = new FormData();
            fd.append("file", metaFile);
            try {
                const apiBase = getApiBaseUrl();
                const resp = await fetch(`${apiBase}/view-metadata`, { method: "POST", body: fd });
                const data = await resp.json();
                if (!resp.ok) throw new Error(data.error || "Etiketler okunamadı.");

                metaTagsList.innerHTML = "";
                const entries = Object.entries(data.tags || {});
                if (entries.length === 0) {
                    metaTagsList.innerHTML = '<p class="text-green-400">✅ Bu görselde gizli EXIF/GPS etiketi bulunamadı. Görsel zaten temiz!</p>';
                } else {
                    entries.forEach(([k, v]) => {
                        const item = document.createElement("div");
                        item.className = "flex justify-between py-1 border-b border-white/5";
                        item.innerHTML = `<span class="text-gray-400">${k}:</span> <span class="text-teal-300 font-semibold truncate max-w-[240px]">${v}</span>`;
                        metaTagsList.appendChild(item);
                    });
                }
                metaReportBox.classList.remove("hidden");
                showToast("info", `🔍 ${data.tag_count} adet metaveri etiketi tarandı.`);
            } catch (err) {
                showToast("error", `⚠️ ${err.message}`);
            }
        });

        btnMetaStrip.addEventListener("click", async () => {
            if (!metaFile) {
                showToast("error", i18n("select_image_error"));
                return;
            }

            // Client-side instant offline stripping in Local Mode
            if (currentMode === 'local') {
                const img = new Image();
                const objUrl = URL.createObjectURL(metaFile);
                img.onload = () => {
                    const canvas = document.createElement('canvas');
                    canvas.width = img.naturalWidth;
                    canvas.height = img.naturalHeight;
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0);
                    canvas.toBlob((blob) => {
                        URL.revokeObjectURL(objUrl);
                        const outName = `clean_${metaFile.name}`;
                        downloadBlob(blob, outName);
                        showToast("success", `🛡️ [Yerel Cihaz] Metaveriler tarayıcıda temizlendi: ${outName}`);
                    }, metaFile.type || 'image/png');
                };
                img.src = objUrl;
                return;
            }

            const fd = new FormData();
            fd.append("file", metaFile);
            try {
                const apiBase = getApiBaseUrl();
                const resp = await fetch(`${apiBase}/strip-metadata`, { method: "POST", body: fd });
                if (!resp.ok) throw new Error("Metaveri temizleme başarısız oldu.");
                const blob = await resp.blob();
                const outName = `clean_${metaFile.name}`;
                downloadBlob(blob, outName);
                showToast("success", `🛡️ Metaveriler silindi ve temiz görsel indirildi: ${outName}`);
            } catch (err) {
                showToast("error", `⚠️ ${err.message}`);
            }
        });
    }

    // ═════════════════════════════════════════════════════════════
    // 4. VIDEO TO GIF / WEBP ANIMATOR
    // ═════════════════════════════════════════════════════════════
    let animFile = null;
    let selectedAnimFormat = "gif";
    const dropAnim = document.getElementById("drop-zone-animator");
    const inputAnim = document.getElementById("file-input-animator");
    const infoAnim = document.getElementById("info-animator");
    const nameAnim = document.getElementById("info-animator-name");
    const sizeAnim = document.getElementById("info-animator-size");
    const btnAnimClear = document.getElementById("btn-animator-clear");
    const btnAnimApply = document.getElementById("btn-animator-apply");
    const animFormatBtns = document.querySelectorAll(".anim-format-btn");
    const animStart = document.getElementById("anim-start");
    const animDuration = document.getElementById("anim-duration");
    const animFps = document.getElementById("anim-fps");
    const animWidth = document.getElementById("anim-width");

    if (dropAnim && inputAnim) {
        dropAnim.addEventListener("click", (e) => {
            if (e.target !== btnAnimClear && !btnAnimClear.contains(e.target)) {
                inputAnim.click();
            }
        });

        inputAnim.addEventListener("change", (e) => {
            if (e.target.files.length) {
                animFile = e.target.files[0];
                nameAnim.textContent = animFile.name;
                sizeAnim.textContent = formatBytes(animFile.size);
                infoAnim.classList.remove("hidden");
            }
        });

        btnAnimClear.addEventListener("click", (e) => {
            e.stopPropagation();
            animFile = null;
            inputAnim.value = "";
            infoAnim.classList.add("hidden");
        });

        animFormatBtns.forEach(btn => {
            btn.addEventListener("click", () => {
                animFormatBtns.forEach(b => {
                    b.className = "anim-format-btn py-3 px-4 rounded-xl border border-white/10 bg-white/5 text-gray-300 font-semibold text-sm hover:border-white/20";
                });
                btn.className = "anim-format-btn py-3 px-4 rounded-xl border border-orange-500 bg-orange-500/20 text-white font-bold text-sm";
                selectedAnimFormat = btn.dataset.format;
            });
        });

        btnAnimApply.addEventListener("click", async () => {
            if (!animFile) {
                showToast("error", i18n("select_video_error"));
                return;
            }

            const taskId = generateTaskId();
            btnAnimApply.disabled = true;
            startGlobalProgress(taskId);

            const fd = new FormData();
            fd.append("file", animFile);
            fd.append("start_time", animStart ? animStart.value : "00:00:00");
            fd.append("duration", animDuration ? animDuration.value : "5");
            fd.append("fps", animFps ? animFps.value : "15");
            fd.append("width", animWidth ? animWidth.value : "480");
            fd.append("anim_format", selectedAnimFormat);
            fd.append("quality", "80");

            try {
                const apiBase = getApiBaseUrl();
                const resp = await fetch(`${apiBase}/video-to-anim`, {
                    method: "POST",
                    headers: { "X-Task-ID": taskId },
                    body: fd
                });
                if (!resp.ok) {
                    const err = await resp.json().catch(() => ({}));
                    throw new Error(err.message || "Animasyon oluşturma başarısız oldu.");
                }
                const blob = await resp.blob();
                const outName = `${animFile.name.replace(/\.[^.]+$/, "")}_anim.${selectedAnimFormat}`;
                downloadBlob(blob, outName);
                stopGlobalProgress(true, "Animasyon Başarıyla Üretildi!");
                showToast("success", `🎞️ Animasyon indirildi: ${outName}`);
            } catch (err) {
                stopGlobalProgress(false);
                showToast("error", `⚠️ ${err.message}`);
            } finally {
                btnAnimApply.disabled = false;
            }
        });
    }

    // ═════════════════════════════════════════════════════════════════
    // 11. SUBTITLE BURNER
    // ═════════════════════════════════════════════════════════════════
    let subVideoFile = null;
    let subSrtFile = null;

    const dropSubVideo = document.getElementById("drop-zone-subtitles-video");
    const inputSubVideo = document.getElementById("file-input-subtitles-video");
    const infoSubVideo = document.getElementById("info-subtitles-video");
    const nameSubVideo = document.getElementById("info-subtitles-video-name");
    const sizeSubVideo = document.getElementById("info-subtitles-video-size");
    const btnSubVideoClear = document.getElementById("btn-subtitles-video-clear");

    const dropSubSub = document.getElementById("drop-zone-subtitles-sub");
    const inputSubSub = document.getElementById("file-input-subtitles-sub");
    const infoSubSub = document.getElementById("info-subtitles-sub");
    const nameSubSub = document.getElementById("info-subtitles-sub-name");
    const sizeSubSub = document.getElementById("info-subtitles-sub-size");
    const btnSubSubClear = document.getElementById("btn-subtitles-sub-clear");

    const selectSubFontSize = document.getElementById("sub-fontsize");
    const selectSubFontColor = document.getElementById("sub-fontcolor");
    const btnSubApply = document.getElementById("btn-subtitles-apply");

    if (dropSubVideo && inputSubVideo) {
        dropSubVideo.addEventListener("click", (e) => {
            if (e.target !== btnSubVideoClear && !btnSubVideoClear?.contains(e.target)) {
                inputSubVideo.click();
            }
        });
        inputSubVideo.addEventListener("change", () => {
            if (inputSubVideo.files && inputSubVideo.files[0]) {
                subVideoFile = inputSubVideo.files[0];
                if (nameSubVideo) nameSubVideo.textContent = subVideoFile.name;
                if (sizeSubVideo) sizeSubVideo.textContent = formatBytes(subVideoFile.size);
                if (infoSubVideo) infoSubVideo.classList.remove("hidden");
            }
        });
        btnSubVideoClear?.addEventListener("click", (e) => {
            e.stopPropagation();
            subVideoFile = null;
            inputSubVideo.value = "";
            if (infoSubVideo) infoSubVideo.classList.add("hidden");
        });
        ['dragenter', 'dragover'].forEach(eventName => {
            dropSubVideo.addEventListener(eventName, (e) => { e.preventDefault(); dropSubVideo.classList.add('border-indigo-500'); });
        });
        ['dragleave', 'drop'].forEach(eventName => {
            dropSubVideo.addEventListener(eventName, (e) => { e.preventDefault(); dropSubVideo.classList.remove('border-indigo-500'); });
        });
        dropSubVideo.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            if (dt && dt.files && dt.files[0]) {
                subVideoFile = dt.files[0];
                if (nameSubVideo) nameSubVideo.textContent = subVideoFile.name;
                if (sizeSubVideo) sizeSubVideo.textContent = formatBytes(subVideoFile.size);
                if (infoSubVideo) infoSubVideo.classList.remove("hidden");
            }
        });
    }

    if (dropSubSub && inputSubSub) {
        dropSubSub.addEventListener("click", (e) => {
            if (e.target !== btnSubSubClear && !btnSubSubClear?.contains(e.target)) {
                inputSubSub.click();
            }
        });
        inputSubSub.addEventListener("change", () => {
            if (inputSubSub.files && inputSubSub.files[0]) {
                subSrtFile = inputSubSub.files[0];
                if (nameSubSub) nameSubSub.textContent = subSrtFile.name;
                if (sizeSubSub) sizeSubSub.textContent = formatBytes(subSrtFile.size);
                if (infoSubSub) infoSubSub.classList.remove("hidden");
            }
        });
        btnSubSubClear?.addEventListener("click", (e) => {
            e.stopPropagation();
            subSrtFile = null;
            inputSubSub.value = "";
            if (infoSubSub) infoSubSub.classList.add("hidden");
        });
        ['dragenter', 'dragover'].forEach(eventName => {
            dropSubSub.addEventListener(eventName, (e) => { e.preventDefault(); dropSubSub.classList.add('border-indigo-500'); });
        });
        ['dragleave', 'drop'].forEach(eventName => {
            dropSubSub.addEventListener(eventName, (e) => { e.preventDefault(); dropSubSub.classList.remove('border-indigo-500'); });
        });
        dropSubSub.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            if (dt && dt.files && dt.files[0]) {
                subSrtFile = dt.files[0];
                if (nameSubSub) nameSubSub.textContent = subSrtFile.name;
                if (sizeSubSub) sizeSubSub.textContent = formatBytes(subSrtFile.size);
                if (infoSubSub) infoSubSub.classList.remove("hidden");
            }
        });
    }

    if (btnSubApply) {
        btnSubApply.addEventListener("click", async () => {
            if (!subVideoFile) {
                showToast("error", i18n("select_video_error"));
                return;
            }
            if (!subSrtFile) {
                showToast("error", i18n("select_sub_error"));
                return;
            }

            const taskId = generateTaskId();
            btnSubApply.disabled = true;
            startGlobalProgress(taskId);

            const fd = new FormData();
            fd.append("video", subVideoFile);
            fd.append("subtitle", subSrtFile);
            fd.append("font_size", selectSubFontSize ? selectSubFontSize.value : "24");
            fd.append("font_color", selectSubFontColor ? selectSubFontColor.value : "&H00FFFFFF");

            try {
                const apiBase = getApiBaseUrl();
                const resp = await fetch(`${apiBase}/burn-subtitles`, {
                    method: "POST",
                    headers: { "X-Task-ID": taskId },
                    body: fd
                });
                if (!resp.ok) {
                    const err = await resp.json().catch(() => ({}));
                    throw new Error(err.message || "Altyazı gömme işlemi başarısız oldu.");
                }
                const blob = await resp.blob();
                const outName = `${subVideoFile.name.replace(/\.[^.]+$/, "")}_subtitled.mp4`;
                downloadBlob(blob, outName);
                stopGlobalProgress(true, "Altyazı Başarıyla Gömdü!");
                showToast("success", `🎬 Altyazılı video indirildi: ${outName}`);
            } catch (err) {
                stopGlobalProgress(false);
                showToast("error", `⚠️ ${err.message}`);
            } finally {
                btnSubApply.disabled = false;
            }
        });
    }

    // ═════════════════════════════════════════════════════════════════
    // 12. PDF TOOLKIT
    // ═════════════════════════════════════════════════════════════════
    let pdfMergeFiles = [];
    let pdfSplitFile = null;
    let pdfTextFile = null;

    const pdfTabs = document.querySelectorAll(".pdf-mode-tab");
    const pdfPanels = {
        merge: document.getElementById("panel-pdf-merge"),
        split: document.getElementById("panel-pdf-split"),
        text: document.getElementById("panel-pdf-text")
    };

    pdfTabs.forEach(tab => {
        tab.addEventListener("click", () => {
            const mode = tab.dataset.mode;
            pdfTabs.forEach(t => {
                t.className = "pdf-mode-tab flex-1 py-2.5 px-3 rounded-xl font-medium text-xs transition-all text-gray-400 hover:text-white flex items-center justify-center gap-1.5";
            });
            tab.className = "pdf-mode-tab flex-1 py-2.5 px-3 rounded-xl font-bold text-xs transition-all bg-red-600 text-white shadow-md flex items-center justify-center gap-1.5";
            Object.values(pdfPanels).forEach(p => p && p.classList.add("hidden"));
            if (pdfPanels[mode]) pdfPanels[mode].classList.remove("hidden");
        });
    });

    const dropPdfMerge = document.getElementById("drop-zone-pdf-merge");
    const inputPdfMerge = document.getElementById("file-input-pdf-merge");
    const listPdfMerge = document.getElementById("pdf-merge-list");
    const btnPdfMergeApply = document.getElementById("btn-pdf-merge-apply");

    function renderPdfMergeList() {
        if (!listPdfMerge) return;
        if (pdfMergeFiles.length === 0) {
            listPdfMerge.classList.add("hidden");
            listPdfMerge.innerHTML = "";
            return;
        }
        listPdfMerge.classList.remove("hidden");
        listPdfMerge.innerHTML = pdfMergeFiles.map((f, idx) => `
            <div class="flex items-center justify-between bg-black/40 border border-white/10 px-3 py-2 rounded-xl text-xs text-white">
                <span class="truncate max-w-[280px]">📄 ${idx + 1}. ${f.name}</span>
                <span class="text-gray-400 text-[11px]">${formatBytes(f.size)}</span>
            </div>
        `).join("");
    }

    if (dropPdfMerge && inputPdfMerge) {
        dropPdfMerge.addEventListener("click", () => inputPdfMerge.click());
        inputPdfMerge.addEventListener("change", () => {
            if (inputPdfMerge.files) {
                pdfMergeFiles = Array.from(inputPdfMerge.files);
                renderPdfMergeList();
            }
        });
        ['dragenter', 'dragover'].forEach(eventName => {
            dropPdfMerge.addEventListener(eventName, (e) => { e.preventDefault(); dropPdfMerge.classList.add('border-red-500'); });
        });
        ['dragleave', 'drop'].forEach(eventName => {
            dropPdfMerge.addEventListener(eventName, (e) => { e.preventDefault(); dropPdfMerge.classList.remove('border-red-500'); });
        });
        dropPdfMerge.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            if (dt && dt.files) {
                pdfMergeFiles = Array.from(dt.files).filter(f => f.name.toLowerCase().endsWith('.pdf'));
                renderPdfMergeList();
            }
        });
    }

    if (btnPdfMergeApply) {
        btnPdfMergeApply.addEventListener("click", async () => {
            if (pdfMergeFiles.length < 2) {
                showToast("error", i18n("select_two_pdf_error"));
                return;
            }
            const taskId = generateTaskId();
            btnPdfMergeApply.disabled = true;
            startGlobalProgress(taskId);

            const fd = new FormData();
            pdfMergeFiles.forEach(f => fd.append("files", f));

            try {
                const apiBase = getApiBaseUrl();
                const resp = await fetch(`${apiBase}/pdf-merge`, {
                    method: "POST",
                    headers: { "X-Task-ID": taskId },
                    body: fd
                });
                if (!resp.ok) {
                    const err = await resp.json().catch(() => ({}));
                    throw new Error(err.message || "PDF birleştirme hatası.");
                }
                const blob = await resp.blob();
                downloadBlob(blob, "birlestirilmis_belge.pdf");
                stopGlobalProgress(true, "PDF'ler Başarıyla Birleştirildi!");
                showToast("success", "📄 Birleştirilmiş PDF indirildi!");
            } catch (err) {
                stopGlobalProgress(false);
                showToast("error", `⚠️ ${err.message}`);
            } finally {
                btnPdfMergeApply.disabled = false;
            }
        });
    }

    const dropPdfSplit = document.getElementById("drop-zone-pdf-split");
    const inputPdfSplit = document.getElementById("file-input-pdf-split");
    const infoPdfSplit = document.getElementById("info-pdf-split");
    const namePdfSplit = document.getElementById("info-pdf-split-name");
    const sizePdfSplit = document.getElementById("info-pdf-split-size");
    const btnPdfSplitClear = document.getElementById("btn-pdf-split-clear");
    const inputPdfPages = document.getElementById("pdf-split-pages");
    const btnPdfSplitApply = document.getElementById("btn-pdf-split-apply");

    if (dropPdfSplit && inputPdfSplit) {
        dropPdfSplit.addEventListener("click", (e) => {
            if (e.target !== btnPdfSplitClear && !btnPdfSplitClear?.contains(e.target)) {
                inputPdfSplit.click();
            }
        });
        inputPdfSplit.addEventListener("change", () => {
            if (inputPdfSplit.files && inputPdfSplit.files[0]) {
                pdfSplitFile = inputPdfSplit.files[0];
                if (namePdfSplit) namePdfSplit.textContent = pdfSplitFile.name;
                if (sizePdfSplit) sizePdfSplit.textContent = formatBytes(pdfSplitFile.size);
                if (infoPdfSplit) infoPdfSplit.classList.remove("hidden");
            }
        });
        btnPdfSplitClear?.addEventListener("click", (e) => {
            e.stopPropagation();
            pdfSplitFile = null;
            inputPdfSplit.value = "";
            if (infoPdfSplit) infoPdfSplit.classList.add("hidden");
        });
        ['dragenter', 'dragover'].forEach(eventName => {
            dropPdfSplit.addEventListener(eventName, (e) => { e.preventDefault(); dropPdfSplit.classList.add('border-red-500'); });
        });
        ['dragleave', 'drop'].forEach(eventName => {
            dropPdfSplit.addEventListener(eventName, (e) => { e.preventDefault(); dropPdfSplit.classList.remove('border-red-500'); });
        });
        dropPdfSplit.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            if (dt && dt.files && dt.files[0]) {
                pdfSplitFile = dt.files[0];
                if (namePdfSplit) namePdfSplit.textContent = pdfSplitFile.name;
                if (sizePdfSplit) sizePdfSplit.textContent = formatBytes(pdfSplitFile.size);
                if (infoPdfSplit) infoPdfSplit.classList.remove("hidden");
            }
        });
    }

    if (btnPdfSplitApply) {
        btnPdfSplitApply.addEventListener("click", async () => {
            if (!pdfSplitFile) {
                showToast("error", i18n("select_split_pdf_error"));
                return;
            }
            const pages = inputPdfPages ? inputPdfPages.value.trim() : "";
            if (!pages) {
                showToast("error", "Lütfen çıkarılacak sayfa veya aralıkları girin (Örn: 1-3).");
                return;
            }

            const taskId = generateTaskId();
            btnPdfSplitApply.disabled = true;
            startGlobalProgress(taskId);

            const fd = new FormData();
            fd.append("file", pdfSplitFile);
            fd.append("page_ranges", pages);

            try {
                const apiBase = getApiBaseUrl();
                const resp = await fetch(`${apiBase}/pdf-split`, {
                    method: "POST",
                    headers: { "X-Task-ID": taskId },
                    body: fd
                });
                if (!resp.ok) {
                    const err = await resp.json().catch(() => ({}));
                    throw new Error(err.message || "Sayfa bölme işlemi başarısız.");
                }
                const blob = await resp.blob();
                const outName = `${pdfSplitFile.name.replace(/\.[^.]+$/, "")}_sayfalar.pdf`;
                downloadBlob(blob, outName);
                stopGlobalProgress(true, "Sayfalar Başarıyla Çıkarıldı!");
                showToast("success", `✂️ Bölünmüş PDF indirildi: ${outName}`);
            } catch (err) {
                stopGlobalProgress(false);
                showToast("error", `⚠️ ${err.message}`);
            } finally {
                btnPdfSplitApply.disabled = false;
            }
        });
    }

    const dropPdfText = document.getElementById("drop-zone-pdf-text");
    const inputPdfText = document.getElementById("file-input-pdf-text");
    const infoPdfText = document.getElementById("info-pdf-text");
    const namePdfText = document.getElementById("info-pdf-text-name");
    const sizePdfText = document.getElementById("info-pdf-text-size");
    const btnPdfTextClear = document.getElementById("btn-pdf-text-clear");
    const btnPdfTextApply = document.getElementById("btn-pdf-text-apply");
    const boxPdfTextResult = document.getElementById("pdf-text-result-box");
    const contentPdfText = document.getElementById("pdf-text-content");
    const btnCopyPdfText = document.getElementById("btn-copy-pdf-text");
    const btnDownloadPdfText = document.getElementById("btn-download-pdf-text");

    if (dropPdfText && inputPdfText) {
        dropPdfText.addEventListener("click", (e) => {
            if (e.target !== btnPdfTextClear && !btnPdfTextClear?.contains(e.target)) {
                inputPdfText.click();
            }
        });
        inputPdfText.addEventListener("change", () => {
            if (inputPdfText.files && inputPdfText.files[0]) {
                pdfTextFile = inputPdfText.files[0];
                if (namePdfText) namePdfText.textContent = pdfTextFile.name;
                if (sizePdfText) sizePdfText.textContent = formatBytes(pdfTextFile.size);
                if (infoPdfText) infoPdfText.classList.remove("hidden");
            }
        });
        btnPdfTextClear?.addEventListener("click", (e) => {
            e.stopPropagation();
            pdfTextFile = null;
            inputPdfText.value = "";
            if (infoPdfText) infoPdfText.classList.add("hidden");
            if (boxPdfTextResult) boxPdfTextResult.classList.add("hidden");
        });
        ['dragenter', 'dragover'].forEach(eventName => {
            dropPdfText.addEventListener(eventName, (e) => { e.preventDefault(); dropPdfText.classList.add('border-red-500'); });
        });
        ['dragleave', 'drop'].forEach(eventName => {
            dropPdfText.addEventListener(eventName, (e) => { e.preventDefault(); dropPdfText.classList.remove('border-red-500'); });
        });
        dropPdfText.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            if (dt && dt.files && dt.files[0]) {
                pdfTextFile = dt.files[0];
                if (namePdfText) namePdfText.textContent = pdfTextFile.name;
                if (sizePdfText) sizePdfText.textContent = formatBytes(pdfTextFile.size);
                if (infoPdfText) infoPdfText.classList.remove("hidden");
            }
        });
    }

    if (btnPdfTextApply) {
        btnPdfTextApply.addEventListener("click", async () => {
            if (!pdfTextFile) {
                showToast("error", i18n("select_pdf_error"));
                return;
            }
            const taskId = generateTaskId();
            btnPdfTextApply.disabled = true;
            startGlobalProgress(taskId);

            const fd = new FormData();
            fd.append("file", pdfTextFile);

            try {
                const apiBase = getApiBaseUrl();
                const resp = await fetch(`${apiBase}/pdf-extract-text`, {
                    method: "POST",
                    headers: { "X-Task-ID": taskId },
                    body: fd
                });
                if (!resp.ok) {
                    const err = await resp.json().catch(() => ({}));
                    throw new Error(err.message || "PDF metin çıkarma hatası.");
                }
                const data = await resp.json();
                if (contentPdfText) contentPdfText.value = data.text || "";
                if (boxPdfTextResult) boxPdfTextResult.classList.remove("hidden");
                stopGlobalProgress(true, "Metin Başarıyla Çıkarıldı!");
                showToast("success", `📄 ${data.pages || 0} sayfalık metin çıkarıldı!`);
            } catch (err) {
                stopGlobalProgress(false);
                showToast("error", `⚠️ ${err.message}`);
            } finally {
                btnPdfTextApply.disabled = false;
            }
        });
    }

    if (btnCopyPdfText && contentPdfText) {
        btnCopyPdfText.addEventListener("click", () => {
            navigator.clipboard.writeText(contentPdfText.value).then(() => {
                showToast("info", "📋 " + i18n("copied_to_clipboard"));
            });
        });
    }

    if (btnDownloadPdfText && contentPdfText) {
        btnDownloadPdfText.addEventListener("click", () => {
            const blob = new Blob([contentPdfText.value], { type: "text/plain;charset=utf-8" });
            const outName = `${pdfTextFile ? pdfTextFile.name.replace(/\.[^.]+$/, "") : "belge"}_metin.txt`;
            downloadBlob(blob, outName);
        });
    }

    // ═════════════════════════════════════════════════════════════════
    // 13. AUDIO EFFECTS & SPEED
    // ═════════════════════════════════════════════════════════════════
    let audioFxFile = null;
    const dropAudioFx = document.getElementById("drop-zone-audiofx");
    const inputAudioFx = document.getElementById("file-input-audiofx");
    const infoAudioFx = document.getElementById("info-audiofx");
    const nameAudioFx = document.getElementById("info-audiofx-name");
    const sizeAudioFx = document.getElementById("info-audiofx-size");
    const btnAudioFxClear = document.getElementById("btn-audiofx-clear");

    const sliderFxTempo = document.getElementById("slider-fx-tempo");
    const labelFxTempo = document.getElementById("label-fx-tempo");
    const sliderFxPitch = document.getElementById("slider-fx-pitch");
    const labelFxPitch = document.getElementById("label-fx-pitch");
    const checkFxReverb = document.getElementById("check-fx-reverb");
    const btnAudioFxApply = document.getElementById("btn-audiofx-apply");

    const btnPresetSlowed = document.getElementById("btn-preset-slowed");
    const btnPresetNightcore = document.getElementById("btn-preset-nightcore");
    const btnPresetFast = document.getElementById("btn-preset-fast");
    const btnPresetReset = document.getElementById("btn-preset-reset");

    function updateFxLabels() {
        if (sliderFxTempo && labelFxTempo) labelFxTempo.textContent = `${parseFloat(sliderFxTempo.value).toFixed(2)}x`;
        if (sliderFxPitch && labelFxPitch) labelFxPitch.textContent = `${parseFloat(sliderFxPitch.value).toFixed(2)}x`;
    }

    sliderFxTempo?.addEventListener("input", updateFxLabels);
    sliderFxPitch?.addEventListener("input", updateFxLabels);

    btnPresetSlowed?.addEventListener("click", () => {
        if (sliderFxTempo) sliderFxTempo.value = "0.85";
        if (sliderFxPitch) sliderFxPitch.value = "0.85";
        if (checkFxReverb) checkFxReverb.checked = true;
        updateFxLabels();
        showToast("info", "🐌 " + i18n("preset_slowed_loaded"));
    });

    btnPresetNightcore?.addEventListener("click", () => {
        if (sliderFxTempo) sliderFxTempo.value = "1.25";
        if (sliderFxPitch) sliderFxPitch.value = "1.25";
        if (checkFxReverb) checkFxReverb.checked = false;
        updateFxLabels();
        showToast("info", "🐿️ " + i18n("preset_nightcore_loaded"));
    });

    btnPresetFast?.addEventListener("click", () => {
        if (sliderFxTempo) sliderFxTempo.value = "1.25";
        if (sliderFxPitch) sliderFxPitch.value = "1.00";
        if (checkFxReverb) checkFxReverb.checked = false;
        updateFxLabels();
        showToast("info", "⚡ " + i18n("preset_fast_loaded"));
    });

    btnPresetReset?.addEventListener("click", () => {
        if (sliderFxTempo) sliderFxTempo.value = "1.00";
        if (sliderFxPitch) sliderFxPitch.value = "1.00";
        if (checkFxReverb) checkFxReverb.checked = false;
        updateFxLabels();
        showToast("info", "🔄 Standart (1.0x) sıfırlandı");
    });

    if (dropAudioFx && inputAudioFx) {
        dropAudioFx.addEventListener("click", (e) => {
            if (e.target !== btnAudioFxClear && !btnAudioFxClear?.contains(e.target)) {
                inputAudioFx.click();
            }
        });
        inputAudioFx.addEventListener("change", () => {
            if (inputAudioFx.files && inputAudioFx.files[0]) {
                audioFxFile = inputAudioFx.files[0];
                if (nameAudioFx) nameAudioFx.textContent = audioFxFile.name;
                if (sizeAudioFx) sizeAudioFx.textContent = formatBytes(audioFxFile.size);
                if (infoAudioFx) infoAudioFx.classList.remove("hidden");
            }
        });
        btnAudioFxClear?.addEventListener("click", (e) => {
            e.stopPropagation();
            audioFxFile = null;
            inputAudioFx.value = "";
            if (infoAudioFx) infoAudioFx.classList.add("hidden");
        });
        ['dragenter', 'dragover'].forEach(eventName => {
            dropAudioFx.addEventListener(eventName, (e) => { e.preventDefault(); dropAudioFx.classList.add('border-emerald-500'); });
        });
        ['dragleave', 'drop'].forEach(eventName => {
            dropAudioFx.addEventListener(eventName, (e) => { e.preventDefault(); dropAudioFx.classList.remove('border-emerald-500'); });
        });
        dropAudioFx.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            if (dt && dt.files && dt.files[0]) {
                audioFxFile = dt.files[0];
                if (nameAudioFx) nameAudioFx.textContent = audioFxFile.name;
                if (sizeAudioFx) sizeAudioFx.textContent = formatBytes(audioFxFile.size);
                if (infoAudioFx) infoAudioFx.classList.remove("hidden");
            }
        });
    }

    if (btnAudioFxApply) {
        btnAudioFxApply.addEventListener("click", async () => {
            if (!audioFxFile) {
                showToast("error", i18n("select_audio_video_error"));
                return;
            }
            const taskId = generateTaskId();
            btnAudioFxApply.disabled = true;
            startGlobalProgress(taskId);

            const fd = new FormData();
            fd.append("file", audioFxFile);
            fd.append("tempo", sliderFxTempo ? sliderFxTempo.value : "1.0");
            fd.append("pitch", sliderFxPitch ? sliderFxPitch.value : "1.0");
            fd.append("reverb", checkFxReverb && checkFxReverb.checked ? "true" : "false");

            try {
                const apiBase = getApiBaseUrl();
                const resp = await fetch(`${apiBase}/audio-effects`, {
                    method: "POST",
                    headers: { "X-Task-ID": taskId },
                    body: fd
                });
                if (!resp.ok) {
                    const err = await resp.json().catch(() => ({}));
                    throw new Error(err.message || "Ses efekti uygulama başarısız.");
                }
                const blob = await resp.blob();
                const outName = `${audioFxFile.name.replace(/\.[^.]+$/, "")}_fx.mp3`;
                downloadBlob(blob, outName);
                stopGlobalProgress(true, "Efekt Başarıyla Uygulandı!");
                showToast("success", `🎵 Efektli ses indirildi: ${outName}`);
            } catch (err) {
                stopGlobalProgress(false);
                showToast("error", `⚠️ ${err.message}`);
            } finally {
                btnAudioFxApply.disabled = false;
            }
        });
    }

    // ═════════════════════════════════════════════════════════════════
    // 14. NOISE CLEANER
    // ═════════════════════════════════════════════════════════════════
    let noiseCleanerFile = null;
    const dropNoise = document.getElementById("drop-zone-noisecleaner");
    const inputNoise = document.getElementById("file-input-noisecleaner");
    const infoNoise = document.getElementById("info-noisecleaner");
    const nameNoise = document.getElementById("info-noisecleaner-name");
    const sizeNoise = document.getElementById("info-noisecleaner-size");
    const btnNoiseClear = document.getElementById("btn-noisecleaner-clear");

    const sliderNoiseNr = document.getElementById("slider-noise-nr");
    const labelNoiseStrength = document.getElementById("label-noise-strength");
    const checkNoiseVoiceFocus = document.getElementById("check-noise-voice-focus");
    const btnNoiseApply = document.getElementById("btn-noisecleaner-apply");

    sliderNoiseNr?.addEventListener("input", () => {
        if (labelNoiseStrength) {
            const val = parseInt(sliderNoiseNr.value, 10);
            let desc = "Dengeli";
            if (val <= 8) desc = "Hafif";
            else if (val >= 20) desc = "Yoğun Filtre";
            labelNoiseStrength.textContent = `${val} dB (${desc})`;
        }
    });

    if (dropNoise && inputNoise) {
        dropNoise.addEventListener("click", (e) => {
            if (e.target !== btnNoiseClear && !btnNoiseClear?.contains(e.target)) {
                inputNoise.click();
            }
        });
        inputNoise.addEventListener("change", () => {
            if (inputNoise.files && inputNoise.files[0]) {
                noiseCleanerFile = inputNoise.files[0];
                if (nameNoise) nameNoise.textContent = noiseCleanerFile.name;
                if (sizeNoise) sizeNoise.textContent = formatBytes(noiseCleanerFile.size);
                if (infoNoise) infoNoise.classList.remove("hidden");
            }
        });
        btnNoiseClear?.addEventListener("click", (e) => {
            e.stopPropagation();
            noiseCleanerFile = null;
            inputNoise.value = "";
            if (infoNoise) infoNoise.classList.add("hidden");
        });
        ['dragenter', 'dragover'].forEach(eventName => {
            dropNoise.addEventListener(eventName, (e) => { e.preventDefault(); dropNoise.classList.add('border-sky-500'); });
        });
        ['dragleave', 'drop'].forEach(eventName => {
            dropNoise.addEventListener(eventName, (e) => { e.preventDefault(); dropNoise.classList.remove('border-sky-500'); });
        });
        dropNoise.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            if (dt && dt.files && dt.files[0]) {
                noiseCleanerFile = dt.files[0];
                if (nameNoise) nameNoise.textContent = noiseCleanerFile.name;
                if (sizeNoise) sizeNoise.textContent = formatBytes(noiseCleanerFile.size);
                if (infoNoise) infoNoise.classList.remove("hidden");
            }
        });
    }

    if (btnNoiseApply) {
        btnNoiseApply.addEventListener("click", async () => {
            if (!noiseCleanerFile) {
                showToast("error", i18n("select_audio_video_error"));
                return;
            }
            const taskId = generateTaskId();
            btnNoiseApply.disabled = true;
            startGlobalProgress(taskId);

            const fd = new FormData();
            fd.append("file", noiseCleanerFile);
            fd.append("noise_reduction_db", sliderNoiseNr ? sliderNoiseNr.value : "12");
            fd.append("voice_focus", checkNoiseVoiceFocus && checkNoiseVoiceFocus.checked ? "true" : "false");

            try {
                const apiBase = getApiBaseUrl();
                const resp = await fetch(`${apiBase}/clean-audio-noise`, {
                    method: "POST",
                    headers: { "X-Task-ID": taskId },
                    body: fd
                });
                if (!resp.ok) {
                    const err = await resp.json().catch(() => ({}));
                    throw new Error(err.message || "Dip gürültü temizleme hatası.");
                }
                const blob = await resp.blob();
                const outName = `${noiseCleanerFile.name.replace(/\.[^.]+$/, "")}_temiz.mp3`;
                downloadBlob(blob, outName);
                stopGlobalProgress(true, "Gürültü Başarıyla Temizlendi!");
                showToast("success", `✨ Temizlenmiş ses indirildi: ${outName}`);
            } catch (err) {
                stopGlobalProgress(false);
                showToast("error", `⚠️ ${err.message}`);
            } finally {
                btnNoiseApply.disabled = false;
            }
        });
    }

});

window.purgeVram = async function() {
    const btn = document.getElementById('btn-purge-vram');
    const btnHome = document.getElementById('btn-purge-vram-home');
    if (btn) btn.disabled = true;
    if (btnHome) btnHome.disabled = true;

    try {
        const apiBase = getApiBaseUrl();
        const resp = await fetch(`${apiBase}/api/purge-vram`, { method: "POST" });
        if (resp.ok) {
            const data = await resp.json();
            const ramMb = data.status?.ram?.used_mb ? `${data.status.ram.used_mb} MB RAM` : '';
            if (typeof showToast === 'function') {
                showToast("success", `🧹 VRAM ve modeller başarıyla boşaltıldı! (${ramMb})`);
            } else {
                alert("VRAM ve modeller boşaltıldı!");
            }
        } else {
            throw new Error(`HTTP ${resp.status}`);
        }
    } catch (e) {
        if (typeof showToast === 'function') {
            showToast("error", "⚠️ " + i18n("vram_purge_failed"));
        }
    } finally {
        if (btn) btn.disabled = false;
        if (btnHome) btnHome.disabled = false;
    }
};

window.openDeviceModeModal = function() {
    const modal = document.getElementById('device-mode-modal');
    if (!modal) return;
    modal.classList.remove('hidden');
    
    // Fetch LAN IP info from backend if available
    fetch('/api/network-info')
        .then(r => r.json())
        .then(data => {
            const displayEl = document.getElementById('display-lan-url');
            if (displayEl && data.mobile_url) {
                displayEl.textContent = data.mobile_url;
            }
            const inputEl = document.getElementById('input-server-url');
            if (inputEl && !inputEl.value) {
                inputEl.value = customServerUrl || data.mobile_url || window.location.origin;
            }
        })
        .catch(() => {
            const displayEl = document.getElementById('display-lan-url');
            if (displayEl) {
                displayEl.textContent = window.location.origin;
            }
            const inputEl = document.getElementById('input-server-url');
            if (inputEl && !inputEl.value) {
                inputEl.value = customServerUrl || window.location.origin;
            }
        });

    window.selectOperatingMode(currentMode);
};

window.closeDeviceModeModal = function() {
    const modal = document.getElementById('device-mode-modal');
    if (modal) modal.classList.add('hidden');
};

window.selectOperatingMode = function(mode) {
    currentMode = mode;
    const cardPc = document.getElementById('card-mode-pc');
    const cardLocal = document.getElementById('card-mode-local');
    const iconPc = document.getElementById('icon-check-pc');
    const iconLocal = document.getElementById('icon-check-local');
    const secPc = document.getElementById('section-pc-config');
    const secLocal = document.getElementById('section-local-config');

    if (mode === 'pc') {
        if (cardPc) {
            cardPc.className = "p-4 rounded-2xl border-2 border-purple-500 bg-purple-500/10 cursor-pointer transition-all flex flex-col justify-between";
        }
        if (cardLocal) {
            cardLocal.className = "p-4 rounded-2xl border border-white/10 bg-white/5 cursor-pointer transition-all flex flex-col justify-between hover:border-white/20";
        }
        if (iconPc) iconPc.className = "fa-solid fa-circle-check text-purple-400";
        if (iconLocal) iconLocal.className = "fa-regular fa-circle text-gray-500";
        if (secPc) secPc.classList.remove('hidden');
        if (secLocal) secLocal.classList.add('hidden');
    } else {
        if (cardPc) {
            cardPc.className = "p-4 rounded-2xl border border-white/10 bg-white/5 cursor-pointer transition-all flex flex-col justify-between hover:border-white/20";
        }
        if (cardLocal) {
            cardLocal.className = "p-4 rounded-2xl border-2 border-pink-500 bg-pink-500/10 cursor-pointer transition-all flex flex-col justify-between";
        }
        if (iconPc) iconPc.className = "fa-regular fa-circle text-gray-500";
        if (iconLocal) iconLocal.className = "fa-solid fa-circle-check text-pink-400";
        if (secPc) secPc.classList.add('hidden');
        if (secLocal) secLocal.classList.remove('hidden');
    }
};

window.testServerConnection = async function() {
    const inputEl = document.getElementById('input-server-url');
    const msgEl = document.getElementById('connection-status-msg');
    if (!inputEl || !msgEl) return;
    
    let target = inputEl.value.trim().replace(/\/+$/, '');
    if (!target) target = window.location.origin;

    msgEl.innerHTML = `<span class="w-2 h-2 rounded-full bg-yellow-400 animate-ping"></span> Bağlanılıyor: ${target}...`;

    try {
        const resp = await fetch(`${target}/api/network-info`, { method: 'GET', mode: 'cors' });
        if (resp.ok) {
            msgEl.innerHTML = `<span class="w-2 h-2 rounded-full bg-green-400"></span> <span class="text-green-400 font-bold">Başarılı:</span> Sunucu aktif ve yanıt veriyor.`;
        } else {
            msgEl.innerHTML = `<span class="w-2 h-2 rounded-full bg-red-400"></span> <span class="text-red-400 font-bold">Hata:</span> HTTP ${resp.status}`;
        }
    } catch (e) {
        msgEl.innerHTML = `<span class="w-2 h-2 rounded-full bg-red-400"></span> <span class="text-red-400 font-bold">Bağlantı Başarısız:</span> Sunucuya erişilemedi.`;
    }
};

window.copyLanUrl = function() {
    const displayEl = document.getElementById('display-lan-url');
    if (!displayEl) return;
    navigator.clipboard.writeText(displayEl.textContent.trim()).then(() => {
        if (typeof showToast === 'function') {
            showToast("info", "📋 " + i18n("copied_to_clipboard"));
        } else {
            alert("Bağlantı kopyalandı!");
        }
    });
};

window.saveOperatingModeSettings = function() {
    const inputEl = document.getElementById('input-server-url');
    if (inputEl) {
        if (currentMode === 'mobile') {
            customServerUrl = inputEl.value.trim().replace(/\/+$/, '');
            localStorage.setItem('gtoolbox_server_url', customServerUrl);
        } else {
            customServerUrl = '';
            localStorage.removeItem('gtoolbox_server_url');
        }
    }
    localStorage.setItem('gtoolbox_mode', currentMode);

    // Update status badge in header
    const dot = document.getElementById('mode-status-dot');
    const text = document.getElementById('mode-status-text');
    if (dot && text) {
        if (currentMode === 'pc') {
            dot.className = "w-2 h-2 rounded-full bg-green-400";
            text.textContent = "PC Server";
        } else {
            dot.className = "w-2 h-2 rounded-full bg-pink-400";
            text.textContent = "Yerel Mobil";
        }
    }

    window.closeDeviceModeModal();
    if (typeof showToast === 'function') {
        showToast("success", `✅ Mod güncellendi: ${currentMode === 'pc' ? 'PC Sunucusu (GPU)' : 'Yerel Cihaz Modu'}`);
    }
};

// Initial badge render on load
document.addEventListener('DOMContentLoaded', () => {
    const dot = document.getElementById('mode-status-dot');
    const text = document.getElementById('mode-status-text');
    if (dot && text) {
        if (currentMode === 'pc') {
            dot.className = "w-2 h-2 rounded-full bg-green-400";
            text.textContent = "PC Server";
        } else {
            dot.className = "w-2 h-2 rounded-full bg-pink-400";
            text.textContent = "Yerel Mobil";
        }
    }
});

