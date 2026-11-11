package com.gtoolbox.app;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.app.DownloadManager;
import android.content.ActivityNotFoundException;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.text.InputType;
import android.util.Base64;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.webkit.CookieManager;
import android.webkit.JavascriptInterface;
import android.webkit.URLUtil;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import androidx.activity.OnBackPressedCallback;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;

import com.google.mlkit.vision.barcode.common.Barcode;
import com.google.mlkit.vision.codescanner.GmsBarcodeScanner;
import com.google.mlkit.vision.codescanner.GmsBarcodeScannerOptions;
import com.google.mlkit.vision.codescanner.GmsBarcodeScanning;

import java.io.OutputStream;

/**
 * G-Toolbox Android client: a WebView onto the G-Toolbox server running on the
 * user's computer. There is no hard-coded address: on first start (or when the
 * server cannot be reached) a setup screen asks for the pairing link shown on
 * the computer (scan its QR code or paste it).
 */
public class MainActivity extends AppCompatActivity {

    private static final int FILE_CHOOSER_REQUEST = 1001;
    private static final int SAVE_FILE_REQUEST = 1002;
    private static final String PREFS_NAME = "GToolboxPrefs";
    private static final String KEY_SERVER_URL = "server_url";

    private WebView webView;
    private View setupView;
    private EditText setupInput;
    private TextView setupStatus;
    private ValueCallback<Uri[]> uploadCallback;
    private byte[] pendingSaveBytes;
    private String serverOrigin;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        webView = createWebView();
        setupView = createSetupView();

        getOnBackPressedDispatcher().addCallback(this, new OnBackPressedCallback(true) {
            @Override
            public void handleOnBackPressed() {
                if (webView.getParent() != null && webView.canGoBack()) {
                    webView.goBack();
                } else if (setupView.getParent() != null && serverOrigin != null) {
                    showWebView(serverOrigin);
                } else {
                    finish();
                }
            }
        });

        String saved = prefs().getString(KEY_SERVER_URL, null);
        if (saved != null && originOf(saved) != null) {
            showWebView(saved);
        } else {
            showSetup(null);
        }
    }

    // ── Server address handling ─────────────────────────────────────────

    private SharedPreferences prefs() {
        return getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
    }

    /** "http(s)://host[:port]" for a valid http(s) URL, else null. */
    @Nullable
    private static String originOf(String raw) {
        if (raw == null) return null;
        String value = raw.trim();
        if (value.isEmpty()) return null;
        if (!value.startsWith("http://") && !value.startsWith("https://")) value = "http://" + value;
        Uri uri = Uri.parse(value);
        String scheme = uri.getScheme();
        String host = uri.getHost();
        if (host == null || host.isEmpty() || !("http".equals(scheme) || "https".equals(scheme))) return null;
        int port = uri.getPort();
        return scheme + "://" + host + (port > 0 ? ":" + port : "");
    }

    /** Accepts a pairing link (with ?token=) or a bare address; loads it and remembers the origin. */
    private void connectTo(String raw) {
        String origin = originOf(raw);
        if (origin == null) {
            setupStatus.setText("Geçersiz adres. Örnek: http://192.168.1.20:8000/?token=…");
            return;
        }
        String value = raw.trim();
        if (!value.startsWith("http://") && !value.startsWith("https://")) value = "http://" + value;
        prefs().edit().putString(KEY_SERVER_URL, origin).apply();
        showWebView(value);
    }

    // ── Views ───────────────────────────────────────────────────────────

    private void showWebView(String url) {
        serverOrigin = originOf(url);
        if (setupView.getParent() != null) ((ViewGroup) setupView.getParent()).removeView(setupView);
        if (webView.getParent() == null) setContentView(webView);
        webView.loadUrl(url);
    }

    private void showSetup(@Nullable String error) {
        if (webView.getParent() != null) ((ViewGroup) webView.getParent()).removeView(webView);
        if (setupView.getParent() == null) setContentView(setupView);
        String saved = prefs().getString(KEY_SERVER_URL, "");
        if (setupInput.getText().length() == 0 && saved != null) setupInput.setText(saved);
        setupStatus.setText(error == null ? "" : error);
    }

    private View createSetupView() {
        int pad = dp(24);
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(pad, dp(48), pad, pad);
        box.setBackgroundColor(Color.parseColor("#050507"));

        TextView title = text("G-Toolbox", 26, Color.WHITE);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        box.addView(title);

        box.addView(text(
                "Bilgisayarınızda G-Toolbox'u açın → Cihaz Modu → \"LAN erişimini aç\". "
                        + "Ardından orada görünen QR kodunu tarayın ya da eşleştirme bağlantısını aşağıya yapıştırın. "
                        + "Telefon ve bilgisayar aynı Wi-Fi ağında olmalıdır.",
                15, Color.parseColor("#C9D1D9")), margins(0, dp(12), 0, dp(20)));

        Button scan = button("QR kodu tara");
        scan.setOnClickListener(v -> scanQr());
        box.addView(scan);

        setupInput = new EditText(this);
        setupInput.setHint("http://192.168.1.20:8000/?token=…");
        setupInput.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI);
        setupInput.setSingleLine(true);
        setupInput.setTextColor(Color.WHITE);
        setupInput.setHintTextColor(Color.parseColor("#6E7681"));
        box.addView(setupInput, margins(0, dp(20), 0, 0));

        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        Button paste = button("Yapıştır");
        paste.setOnClickListener(v -> {
            ClipboardManager cm = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
            ClipData clip = cm != null ? cm.getPrimaryClip() : null;
            if (clip != null && clip.getItemCount() > 0) {
                CharSequence t = clip.getItemAt(0).coerceToText(this);
                if (t != null) setupInput.setText(t.toString().trim());
            }
        });
        Button connect = button("Bağlan");
        connect.setOnClickListener(v -> connectTo(setupInput.getText().toString()));
        row.addView(paste, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        row.addView(connect, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));
        box.addView(row, margins(0, dp(8), 0, 0));

        setupStatus = text("", 14, Color.parseColor("#F85149"));
        box.addView(setupStatus, margins(0, dp(16), 0, 0));

        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(Color.parseColor("#050507"));
        scroll.addView(box);
        return scroll;
    }

    private void scanQr() {
        GmsBarcodeScannerOptions options = new GmsBarcodeScannerOptions.Builder()
                .setBarcodeFormats(Barcode.FORMAT_QR_CODE)
                .build();
        GmsBarcodeScanner scanner = GmsBarcodeScanning.getClient(this, options);
        scanner.startScan()
                .addOnSuccessListener(barcode -> {
                    String raw = barcode.getRawValue();
                    if (raw != null) {
                        setupInput.setText(raw);
                        connectTo(raw);
                    }
                })
                .addOnFailureListener(e -> setupStatus.setText(
                        "QR tarayıcı açılamadı. Bağlantıyı elle yapıştırabilirsiniz."));
    }

    @SuppressLint("SetJavaScriptEnabled")
    private WebView createWebView() {
        WebView wv = new WebView(this);
        WebSettings s = wv.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        // The page never needs local files or content:// URLs; uploads go through the file chooser.
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(false);
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        s.setLoadWithOverviewMode(true);
        s.setUseWideViewPort(true);
        CookieManager.getInstance().setAcceptCookie(true);

        wv.addJavascriptInterface(new AndroidBridge(), "GToolboxAndroid");

        wv.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                String origin = originOf(uri.toString());
                if (origin != null && origin.equals(serverOrigin)) return false;
                // Anything outside the paired server opens in the user's browser.
                try {
                    startActivity(new Intent(Intent.ACTION_VIEW, uri));
                } catch (ActivityNotFoundException ignored) {
                }
                return true;
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                CookieManager.getInstance().flush();  // keep the pairing cookie
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if (request.isForMainFrame()) {
                    showSetup("Bilgisayara bağlanılamadı (" + error.getDescription() + "). "
                            + "G-Toolbox açık mı, LAN erişimi etkin mi ve aynı Wi-Fi ağında mısınız?");
                }
            }
        });

        wv.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if (uploadCallback != null) uploadCallback.onReceiveValue(null);
                uploadCallback = callback;
                try {
                    startActivityForResult(params.createIntent(), FILE_CHOOSER_REQUEST);
                    return true;
                } catch (ActivityNotFoundException e) {
                    uploadCallback = null;
                    return false;
                }
            }
        });

        // Server-side downloads (e.g. /download-file/<id>): let DownloadManager fetch them
        // with the pairing cookie so large videos never pass through memory.
        wv.setDownloadListener((url, userAgent, contentDisposition, mimeType, contentLength) -> {
            if (!url.startsWith("http://") && !url.startsWith("https://")) return;  // blobs use the bridge
            String name = URLUtil.guessFileName(url, contentDisposition, mimeType);
            DownloadManager.Request req = new DownloadManager.Request(Uri.parse(url));
            String cookie = CookieManager.getInstance().getCookie(url);
            if (cookie != null) req.addRequestHeader("Cookie", cookie);
            req.addRequestHeader("User-Agent", userAgent);
            req.setMimeType(mimeType);
            req.setTitle(name);
            req.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
            req.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, name);
            DownloadManager dm = (DownloadManager) getSystemService(Context.DOWNLOAD_SERVICE);
            if (dm != null) {
                dm.enqueue(req);
                Toast.makeText(this, "İndiriliyor: " + name, Toast.LENGTH_SHORT).show();
            }
        });
        return wv;
    }

    /** Methods callable from the G-Toolbox page as window.GToolboxAndroid.*. */
    private class AndroidBridge {
        /** Saves a result produced in the page (base64) via the system "Save as" screen. */
        @JavascriptInterface
        public void saveFile(String fileName, String mimeType, String base64) {
            final byte[] data;
            try {
                data = Base64.decode(base64, Base64.DEFAULT);
            } catch (IllegalArgumentException e) {
                return;
            }
            runOnUiThread(() -> {
                pendingSaveBytes = data;
                Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType(mimeType == null || mimeType.isEmpty() ? "application/octet-stream" : mimeType);
                intent.putExtra(Intent.EXTRA_TITLE, fileName == null ? "dosya" : fileName);
                try {
                    startActivityForResult(intent, SAVE_FILE_REQUEST);
                } catch (ActivityNotFoundException e) {
                    pendingSaveBytes = null;
                    Toast.makeText(MainActivity.this, "Kaydetme ekranı açılamadı.", Toast.LENGTH_LONG).show();
                }
            });
        }

        /** Opens the server address screen (used by the page's device settings). */
        @JavascriptInterface
        public void openServerSettings() {
            runOnUiThread(() -> showSetup(null));
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, @Nullable Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == FILE_CHOOSER_REQUEST) {
            if (uploadCallback == null) return;
            Uri[] results = null;
            if (resultCode == Activity.RESULT_OK && data != null) {
                if (data.getClipData() != null) {
                    int count = data.getClipData().getItemCount();
                    results = new Uri[count];
                    for (int i = 0; i < count; i++) results[i] = data.getClipData().getItemAt(i).getUri();
                } else if (data.getData() != null) {
                    results = new Uri[]{data.getData()};
                }
            }
            uploadCallback.onReceiveValue(results);
            uploadCallback = null;
        } else if (requestCode == SAVE_FILE_REQUEST) {
            byte[] bytes = pendingSaveBytes;
            pendingSaveBytes = null;
            if (resultCode != Activity.RESULT_OK || data == null || data.getData() == null || bytes == null) return;
            try (OutputStream out = getContentResolver().openOutputStream(data.getData())) {
                if (out == null) throw new java.io.IOException("no stream");
                out.write(bytes);
                Toast.makeText(this, "Dosya kaydedildi.", Toast.LENGTH_SHORT).show();
            } catch (Exception e) {
                Toast.makeText(this, "Dosya kaydedilemedi: " + e.getMessage(), Toast.LENGTH_LONG).show();
            }
        }
    }

    // ── Small view helpers ──────────────────────────────────────────────

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    private TextView text(String s, int sp, int color) {
        TextView t = new TextView(this);
        t.setText(s);
        t.setTextSize(sp);
        t.setTextColor(color);
        return t;
    }

    private Button button(String label) {
        Button b = new Button(this);
        b.setText(label);
        b.setAllCaps(false);
        return b;
    }

    private LinearLayout.LayoutParams margins(int l, int t, int r, int b) {
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        p.setMargins(l, t, r, b);
        p.gravity = Gravity.START;
        return p;
    }
}
