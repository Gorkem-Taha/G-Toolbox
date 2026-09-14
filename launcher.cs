using System;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.IO;
using System.IO.Compression;
using System.Net;
using System.Threading;
using System.Windows.Forms;

namespace GToolboxLauncher
{
    // ═════════════════════════════════════════════════════════════════════════
    // 0. ICON & ASSET HELPER (Crisp, High-Resolution Icon Loader)
    // ═════════════════════════════════════════════════════════════════════════
    internal static class IconHelper
    {
        public static void ApplyAppIcon(Form form, PictureBox picBox, string baseDir)
        {
            string icoPath = Path.Combine(baseDir, "static", "favicon.ico");
            if (File.Exists(icoPath))
            {
                try { form.Icon = new Icon(icoPath); } catch { }
            }
            else
            {
                try { form.Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath); } catch { }
            }

            if (picBox != null)
            {
                picBox.SizeMode = PictureBoxSizeMode.Zoom;
                picBox.BackColor = Color.Transparent;
                string pngPath = Path.Combine(baseDir, "static", "icon.png");
                if (File.Exists(pngPath))
                {
                    try
                    {
                        using (Image img = Image.FromFile(pngPath))
                        {
                            picBox.Image = new Bitmap(img);
                        }
                    }
                    catch { }
                }
                if (picBox.Image == null && form.Icon != null)
                {
                    try { picBox.Image = form.Icon.ToBitmap(); } catch { }
                }
            }
        }
    }

    internal class TimeoutWebClient : WebClient
    {
        private int _timeoutMs;
        public TimeoutWebClient(int timeoutMs = 300000) { _timeoutMs = timeoutMs; }
        protected override WebRequest GetWebRequest(Uri uri)
        {
            WebRequest w = base.GetWebRequest(uri);
            w.Timeout = _timeoutMs;
            HttpWebRequest http = w as HttpWebRequest;
            if (http != null)
            {
                http.ReadWriteTimeout = _timeoutMs;
            }
            return w;
        }
    }

    // ═════════════════════════════════════════════════════════════════════════
    // 1. SETUP / DOWNLOAD WIZARD FORM (Portable Python 3.10 & Runtime Engine)
    // ═════════════════════════════════════════════════════════════════════════
    public class SetupForm : Form
    {
        private Label lblTitle;
        private Label lblSubtitle;
        private Label lblStatus;
        private Label lblDetail;
        private Label lblClose;
        private ProgressBar progressBar;
        private PictureBox picIcon;
        private CheckBox chkInstallAi;
        private Button btnStart;
        private System.Windows.Forms.Timer autoStartTimer;
        private int countdown = 3;
        private bool isInstalling = false;
        private string baseDir;

        public SetupForm(string directory)
        {
            this.baseDir = directory;
            InitUI();
        }

        private void InitUI()
        {
            this.Size = new Size(520, 310);
            this.FormBorderStyle = FormBorderStyle.None;
            this.StartPosition = FormStartPosition.CenterScreen;
            this.TopMost = true;
            this.ShowInTaskbar = true;
            this.BackColor = Color.FromArgb(13, 17, 23); // Dark slate GitHub style

            // Enable double buffering and optimize painting to prevent stutter and lag
            this.SetStyle(ControlStyles.OptimizedDoubleBuffer | ControlStyles.AllPaintingInWmPaint | ControlStyles.UserPaint, true);
            this.DoubleBuffered = true;

            // Custom Paint for border & gradient glow
            this.Paint += (s, e) =>
            {
                Graphics g = e.Graphics;
                g.SmoothingMode = SmoothingMode.AntiAlias;

                using (LinearGradientBrush brush = new LinearGradientBrush(
                    new Rectangle(0, 0, this.Width, 80),
                    Color.FromArgb(40, 99, 102, 241),
                    Color.FromArgb(0, 13, 17, 23),
                    LinearGradientMode.Vertical))
                {
                    g.FillRectangle(brush, 0, 0, this.Width, 80);
                }

                using (Pen borderPen = new Pen(Color.FromArgb(99, 102, 241), 1.5f))
                {
                    g.DrawRectangle(borderPen, 0, 0, this.Width - 1, this.Height - 1);
                }
            };

            // Icon PictureBox setup (crisp display)
            picIcon = new PictureBox();
            picIcon.Size = new Size(52, 52);
            picIcon.Location = new Point(28, 26);
            picIcon.SizeMode = PictureBoxSizeMode.Zoom;
            picIcon.BackColor = Color.Transparent;
            IconHelper.ApplyAppIcon(this, picIcon, baseDir);
            this.Controls.Add(picIcon);

            // Title
            lblTitle = new Label();
            lblTitle.Text = "G-Toolbox Setup";
            lblTitle.Font = new Font("Segoe UI", 18, FontStyle.Bold);
            lblTitle.ForeColor = Color.White;
            lblTitle.Location = new Point(92, 24);
            lblTitle.AutoSize = true;
            this.Controls.Add(lblTitle);

            // Subtitle
            lblSubtitle = new Label();
            lblSubtitle.Text = "Sıfır Kurulum: Taşınabilir Python 3.10 & Temel Motor Hazırlığı";
            lblSubtitle.Font = new Font("Segoe UI", 9.2f, FontStyle.Regular);
            lblSubtitle.ForeColor = Color.FromArgb(148, 163, 184);
            lblSubtitle.Location = new Point(94, 56);
            lblSubtitle.AutoSize = true;
            this.Controls.Add(lblSubtitle);

            // Close (X) button
            lblClose = new Label();
            lblClose.Text = "✕";
            lblClose.Font = new Font("Segoe UI", 11, FontStyle.Bold);
            lblClose.ForeColor = Color.FromArgb(148, 163, 184);
            lblClose.Location = new Point(485, 12);
            lblClose.Size = new Size(24, 24);
            lblClose.Cursor = Cursors.Hand;
            lblClose.Click += (s, e) => { if (!isInstalling) { this.DialogResult = DialogResult.Cancel; this.Close(); } };
            this.Controls.Add(lblClose);

            // Status text
            lblStatus = new Label();
            lblStatus.Text = "Python ortamı bulunamadı. Taşınabilir runtime indirilecek.";
            lblStatus.Font = new Font("Segoe UI", 9.5f, FontStyle.Bold);
            lblStatus.ForeColor = Color.FromArgb(203, 213, 225);
            lblStatus.Location = new Point(30, 102);
            lblStatus.Size = new Size(460, 22);
            this.Controls.Add(lblStatus);

            // Detail text
            lblDetail = new Label();
            lblDetail.Text = "Sisteminiz temiz kalır. Kurulum bittiğinde uygulama otomatik açılır.";
            lblDetail.Font = new Font("Segoe UI", 8.5f, FontStyle.Regular);
            lblDetail.ForeColor = Color.FromArgb(148, 163, 184);
            lblDetail.Location = new Point(30, 126);
            lblDetail.Size = new Size(460, 20);
            this.Controls.Add(lblDetail);

            // Progress Bar
            progressBar = new ProgressBar();
            progressBar.Location = new Point(30, 154);
            progressBar.Size = new Size(460, 8);
            progressBar.Style = ProgressBarStyle.Continuous;
            this.Controls.Add(progressBar);

            // AI Checkbox
            chkInstallAi = new CheckBox();
            chkInstallAi.Text = "Yapay zekâ motorunu da hemen indir (PyTorch CPU ~200MB)";
            chkInstallAi.Font = new Font("Segoe UI", 8.5f, FontStyle.Regular);
            chkInstallAi.ForeColor = Color.FromArgb(203, 213, 225);
            chkInstallAi.Location = new Point(30, 180);
            chkInstallAi.Size = new Size(460, 24);
            chkInstallAi.Checked = false;
            chkInstallAi.CheckedChanged += (s, e) => { StopCountdown(); };
            this.Controls.Add(chkInstallAi);

            // Start Button
            btnStart = new Button();
            btnStart.Text = "Kurulumu Başlat (3s)...";
            btnStart.Font = new Font("Segoe UI", 9.5f, FontStyle.Bold);
            btnStart.ForeColor = Color.White;
            btnStart.BackColor = Color.FromArgb(99, 102, 241);
            btnStart.FlatStyle = FlatStyle.Flat;
            btnStart.FlatAppearance.BorderSize = 0;
            btnStart.Location = new Point(30, 216);
            btnStart.Size = new Size(460, 36);
            btnStart.Cursor = Cursors.Hand;
            btnStart.Click += (s, e) =>
            {
                StopCountdown();
                StartInstallation();
            };
            this.Controls.Add(btnStart);

            // Version info footer
            Label lblVer = new Label();
            lblVer.Text = "G-Toolbox v4.4 • Sıfır Bağımlılık & Taşınabilir Çalışma Ortamı";
            lblVer.Font = new Font("Segoe UI", 8f, FontStyle.Regular);
            lblVer.ForeColor = Color.FromArgb(100, 116, 139);
            lblVer.Location = new Point(30, 264);
            lblVer.AutoSize = true;
            this.Controls.Add(lblVer);

            // Countdown timer for automatic zero-click start
            autoStartTimer = new System.Windows.Forms.Timer();
            autoStartTimer.Interval = 1000;
            autoStartTimer.Tick += (s, e) =>
            {
                countdown--;
                if (countdown > 0)
                {
                    btnStart.Text = string.Format("Kurulumu Başlat ({0}s)...", countdown);
                }
                else
                {
                    StopCountdown();
                    StartInstallation();
                }
            };
            autoStartTimer.Start();
        }

        private void StopCountdown()
        {
            if (autoStartTimer != null)
            {
                autoStartTimer.Stop();
                autoStartTimer.Dispose();
                autoStartTimer = null;
            }
            if (!isInstalling)
            {
                btnStart.Text = "Hızlı Kurulumu Başlat";
            }
        }

        private void StartInstallation()
        {
            if (isInstalling) return;
            isInstalling = true;
            btnStart.Enabled = false;
            chkInstallAi.Enabled = false;
            lblClose.Visible = false;

            Thread worker = new Thread(new ParameterizedThreadStart(RunInstallationWorker));
            worker.IsBackground = true;
            worker.Start(chkInstallAi.Checked);
        }

        private void RunInstallationWorker(object param)
        {
            bool installAi = (bool)param;
            string runtimeDir = Path.Combine(baseDir, "runtime");
            string zipPath = Path.Combine(baseDir, "python_embed.zip");

            try
            {
                ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls12 | (SecurityProtocolType)3072;

                // ── STEP 1: Download Python 3.10.11 Embeddable ZIP ───────
                UpdateUI("1/4: Taşınabilir Python 3.10.11 indiriliyor...", "Resmi Python deposundan paket indiriliyor (~8.2 MB)...", 0, ProgressBarStyle.Continuous);

                string pyUrl = "https://www.python.org/ftp/python/3.10.11/python-3.10.11-embed-amd64.zip";
                using (TimeoutWebClient client = new TimeoutWebClient(300000))
                {
                    long lastProgressTick = 0;
                    int lastPct = -1;
                    client.DownloadProgressChanged += (s, e) =>
                    {
                        long now = Environment.TickCount;
                        if (e.ProgressPercentage != lastPct && (now - lastProgressTick > 80 || e.ProgressPercentage == 100))
                        {
                            lastProgressTick = now;
                            lastPct = e.ProgressPercentage;
                            double mbReceived = e.BytesReceived / 1048576.0;
                            double mbTotal = e.TotalBytesToReceive > 0 ? e.TotalBytesToReceive / 1048576.0 : 8.2;
                            string detail = string.Format("İndirilen: {0:F1} MB / {1:F1} MB (%{2})", mbReceived, mbTotal, e.ProgressPercentage);
                            UpdateUI(null, detail, e.ProgressPercentage, ProgressBarStyle.Continuous);
                        }
                    };

                    client.DownloadFile(new Uri(pyUrl), zipPath);
                }

                // ── STEP 2: Extract to runtime/ ──────────────────────────
                UpdateUI("2/4: Çalışma ortamı runtime/ dizinine çıkartılıyor...", "Lütfen bekleyin, arşiv açılıyor...", 0, ProgressBarStyle.Marquee);

                if (Directory.Exists(runtimeDir))
                {
                    try { Directory.Delete(runtimeDir, true); } catch { }
                }
                Directory.CreateDirectory(runtimeDir);

                ZipFile.ExtractToDirectory(zipPath, runtimeDir);
                try { File.Delete(zipPath); } catch { }

                // ── STEP 3: Configure python310._pth & Pip ───────────────
                UpdateUI("3/4: Paket yolları ve Pip yapılandırılıyor...", "python310._pth dosyasında import site etkinleştiriliyor...", 0, ProgressBarStyle.Marquee);

                string[] pthFiles = Directory.GetFiles(runtimeDir, "python*._pth");
                if (pthFiles.Length > 0)
                {
                    string pthPath = pthFiles[0];
                    // Configure isolated search paths: runtime, root (..), site-packages and enable site.main()
                    string pthContent = "python310.zip\r\n.\r\n..\r\nLib\\site-packages\r\nimport site\r\n";
                    File.WriteAllText(pthPath, pthContent);
                }

                string sitePackages = Path.Combine(runtimeDir, "Lib", "site-packages");
                if (!Directory.Exists(sitePackages)) Directory.CreateDirectory(sitePackages);

                string getPipPath = Path.Combine(runtimeDir, "get-pip.py");
                UpdateUI("3/4: Pip paket yöneticisi indiriliyor...", "bootstrap.pypa.io üzerinden get-pip.py çekiliyor...", 0, ProgressBarStyle.Marquee);
                using (TimeoutWebClient client = new TimeoutWebClient(300000))
                {
                    client.DownloadFile("https://bootstrap.pypa.io/get-pip.py", getPipPath);
                }

                string pythonExe = Path.Combine(runtimeDir, "python.exe");
                UpdateUI("3/4: Pip kuruluyor...", "runtime içine pip ve setuptools yükleniyor...", 0, ProgressBarStyle.Marquee);
                RunProcess(pythonExe, "\"" + getPipPath + "\" --no-warn-script-location --default-timeout 180", runtimeDir);
                try { File.Delete(getPipPath); } catch { }

                // ── STEP 4: Install Core Dependencies ───────────────────
                UpdateUI("4/4: Temel motor paketleri yükleniyor...", "FastAPI, WebView, Medya Araçları ve Bağımlılıklar (1-2 dk)...", 0, ProgressBarStyle.Marquee);

                string corePackages = "fastapi uvicorn python-multipart jinja2 pydantic ffmpeg-python yt-dlp Pillow pyAesCrypt pypdf pywebview opencv-python numpy aiofiles psutil certifi --no-warn-script-location --prefer-binary --default-timeout 180 --retries 5";
                RunProcess(pythonExe, "-m pip install " + corePackages, runtimeDir);

                if (installAi)
                {
                    UpdateUI("4/4+: Yapay Zekâ Motoru kuruluyor (PyTorch)...", "PyTorch CPU bileşenleri indiriliyor (~250 MB)...", 0, ProgressBarStyle.Marquee);
                    RunProcess(pythonExe, "-m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu --no-warn-script-location --prefer-binary --default-timeout 180 --retries 5", runtimeDir);
                    UpdateUI("4/4+: Yapay Zekâ Motoru kuruluyor (BasicSR)...", "BasicSR mimarisi yapılandırılıyor...", 0, ProgressBarStyle.Marquee);
                    RunProcess(pythonExe, "-m pip install basicsr --no-deps --no-warn-script-location --prefer-binary --default-timeout 180 --retries 5", runtimeDir);
                    UpdateUI("4/4+: Yapay Zekâ Motoru kuruluyor (Modüller)...", "RealESRGAN, Rembg, LaMa, Whisper, Demucs yükleniyor...", 0, ProgressBarStyle.Marquee);
                    RunProcess(pythonExe, "-m pip install realesrgan rembg simple-lama-inpainting faster-whisper demucs --no-warn-script-location --prefer-binary --default-timeout 180 --retries 5", runtimeDir);
                }

                // ── STEP 5: Finished! ───────────────────────────────────
                UpdateUI("🎉 Kurulum tamamlandı!", "G-Toolbox başlatılıyor...", 100, ProgressBarStyle.Continuous);
                Thread.Sleep(1200);

                this.Invoke((MethodInvoker)delegate
                {
                    this.DialogResult = DialogResult.OK;
                    this.Close();
                });
            }
            catch (Exception ex)
            {
                this.Invoke((MethodInvoker)delegate
                {
                    MessageBox.Show("Kurulum sırasında bir hata oluştu:\n\n" + ex.Message + "\n\nLütfen internet bağlantınızı kontrol edip tekrar deneyin.", "G-Toolbox Kurulum Hatası", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    isInstalling = false;
                    btnStart.Enabled = true;
                    btnStart.Text = "Yeniden Dene";
                    chkInstallAi.Enabled = true;
                    lblClose.Visible = true;
                    lblStatus.Text = "Kurulum tamamlanamadı.";
                    lblDetail.Text = "Hata: " + ex.Message;
                    progressBar.Style = ProgressBarStyle.Continuous;
                    progressBar.Value = 0;
                });
            }
        }

        private void RunProcess(string exe, string args, string workDir)
        {
            ProcessStartInfo psi = new ProcessStartInfo();
            psi.FileName = exe;
            psi.Arguments = args;
            psi.WorkingDirectory = workDir;
            psi.UseShellExecute = false;
            psi.CreateNoWindow = true;
            psi.RedirectStandardError = true;
            psi.RedirectStandardOutput = true;
            psi.WindowStyle = ProcessWindowStyle.Hidden;

            using (Process p = new Process())
            {
                p.StartInfo = psi;
                System.Text.StringBuilder errBuffer = new System.Text.StringBuilder();
                System.Text.StringBuilder outBuffer = new System.Text.StringBuilder();

                p.OutputDataReceived += (s, e) =>
                {
                    if (e.Data != null)
                    {
                        outBuffer.AppendLine(e.Data);
                        string line = e.Data.Trim();
                        if (line.Length > 0 && !line.StartsWith("["))
                        {
                            string shortLine = line.Length > 60 ? line.Substring(0, 57) + "..." : line;
                            UpdateUI(null, shortLine, -1, ProgressBarStyle.Marquee);
                        }
                    }
                };

                p.ErrorDataReceived += (s, e) =>
                {
                    if (e.Data != null)
                    {
                        errBuffer.AppendLine(e.Data);
                        string line = e.Data.Trim();
                        if (line.Length > 0 && !line.StartsWith("["))
                        {
                            string shortLine = line.Length > 60 ? line.Substring(0, 57) + "..." : line;
                            UpdateUI(null, shortLine, -1, ProgressBarStyle.Marquee);
                        }
                    }
                };

                p.Start();
                p.BeginOutputReadLine();
                p.BeginErrorReadLine();

                // 15 minutes timeout for slow secondary laptops
                if (!p.WaitForExit(900000))
                {
                    try { p.Kill(); } catch { }
                    throw new Exception("İşlem zaman aşımına uğradı (15 dk): " + exe);
                }

                string stderr = errBuffer.ToString();
                if (p.ExitCode != 0 && !string.IsNullOrEmpty(stderr) && (stderr.Contains("ERROR:") || stderr.Contains("Traceback") || stderr.Contains("Fatal error:")))
                {
                    throw new Exception("İşlem hatası (kod " + p.ExitCode + "):\n" + stderr);
                }
            }
        }

        private void UpdateUI(string status, string detail, int progress, ProgressBarStyle style)
        {
            if (this.IsDisposed || !this.IsHandleCreated) return;
            this.Invoke((MethodInvoker)delegate
            {
                if (status != null) lblStatus.Text = status;
                if (detail != null) lblDetail.Text = detail;
                progressBar.Style = style;
                if (style == ProgressBarStyle.Continuous)
                {
                    if (progress >= 0 && progress <= 100) progressBar.Value = progress;
                }
            });
        }
    }

    // ═════════════════════════════════════════════════════════════════════════
    // 2. SPLASH SCREEN FORM (Fast Startup & Readiness Poller)
    // ═════════════════════════════════════════════════════════════════════════
    public class SplashForm : Form
    {
        private Label lblTitle;
        private Label lblSubtitle;
        private Label lblStatus;
        private Label lblVersion;
        private ProgressBar progressBar;
        private PictureBox picIcon;
        private System.Windows.Forms.Timer pollTimer;
        private Process pythonProcess;
        private string baseDir;
        private int checkCount = 0;
        private const int MaxChecks = 150; // ~30 seconds max

        public SplashForm(string directory, Process proc)
        {
            this.baseDir = directory;
            this.pythonProcess = proc;
            InitUI();
        }

        private void InitUI()
        {
            this.Size = new Size(460, 240);
            this.FormBorderStyle = FormBorderStyle.None;
            this.StartPosition = FormStartPosition.CenterScreen;
            this.TopMost = true;
            this.ShowInTaskbar = true;
            this.BackColor = Color.FromArgb(13, 17, 23);

            this.SetStyle(ControlStyles.OptimizedDoubleBuffer | ControlStyles.AllPaintingInWmPaint | ControlStyles.UserPaint, true);
            this.DoubleBuffered = true;

            this.Paint += (s, e) =>
            {
                Graphics g = e.Graphics;
                g.SmoothingMode = SmoothingMode.AntiAlias;

                using (LinearGradientBrush brush = new LinearGradientBrush(
                    new Rectangle(0, 0, this.Width, 80),
                    Color.FromArgb(40, 99, 102, 241),
                    Color.FromArgb(0, 13, 17, 23),
                    LinearGradientMode.Vertical))
                {
                    g.FillRectangle(brush, 0, 0, this.Width, 80);
                }

                using (Pen borderPen = new Pen(Color.FromArgb(99, 102, 241), 1.5f))
                {
                    g.DrawRectangle(borderPen, 0, 0, this.Width - 1, this.Height - 1);
                }
            };

            picIcon = new PictureBox();
            picIcon.Size = new Size(54, 54);
            picIcon.Location = new Point(28, 30);
            picIcon.SizeMode = PictureBoxSizeMode.Zoom;
            picIcon.BackColor = Color.Transparent;
            IconHelper.ApplyAppIcon(this, picIcon, baseDir);
            this.Controls.Add(picIcon);

            lblTitle = new Label();
            lblTitle.Text = "G-Toolbox";
            lblTitle.Font = new Font("Segoe UI", 19, FontStyle.Bold);
            lblTitle.ForeColor = Color.White;
            lblTitle.Location = new Point(94, 28);
            lblTitle.AutoSize = true;
            this.Controls.Add(lblTitle);

            lblSubtitle = new Label();
            lblSubtitle.Text = "All-in-One Media & AI Studio";
            lblSubtitle.Font = new Font("Segoe UI", 9.5f, FontStyle.Regular);
            lblSubtitle.ForeColor = Color.FromArgb(148, 163, 184);
            lblSubtitle.Location = new Point(96, 62);
            lblSubtitle.AutoSize = true;
            this.Controls.Add(lblSubtitle);

            lblStatus = new Label();
            lblStatus.Text = "Yapay zekâ ve medya motorları başlatılıyor...";
            lblStatus.Font = new Font("Segoe UI", 9.5f, FontStyle.Regular);
            lblStatus.ForeColor = Color.FromArgb(203, 213, 225);
            lblStatus.Location = new Point(30, 120);
            lblStatus.Size = new Size(400, 24);
            this.Controls.Add(lblStatus);

            progressBar = new ProgressBar();
            progressBar.Style = ProgressBarStyle.Marquee;
            progressBar.MarqueeAnimationSpeed = 25;
            progressBar.Location = new Point(30, 150);
            progressBar.Size = new Size(400, 7);
            this.Controls.Add(progressBar);

            lblVersion = new Label();
            lblVersion.Text = "v4.4 Desktop • Lütfen bekleyin...";
            lblVersion.Font = new Font("Segoe UI", 8.5f, FontStyle.Regular);
            lblVersion.ForeColor = Color.FromArgb(100, 116, 139);
            lblVersion.Location = new Point(30, 175);
            lblVersion.AutoSize = true;
            this.Controls.Add(lblVersion);

            pollTimer = new System.Windows.Forms.Timer();
            pollTimer.Interval = 250;
            pollTimer.Tick += PollTimer_Tick;
            pollTimer.Start();
        }

        private void PollTimer_Tick(object sender, EventArgs e)
        {
            checkCount++;

            if (pythonProcess != null && pythonProcess.HasExited)
            {
                pollTimer.Stop();
                string details = "";
                string errFile = Path.Combine(baseDir, "desktop_error.log");
                if (File.Exists(errFile))
                {
                    try { details = "\n\nHata Ayrıntısı:\n" + File.ReadAllText(errFile).Trim(); } catch { }
                }
                if (string.IsNullOrEmpty(details))
                {
                    string logFile = Path.Combine(baseDir, "desktop.log");
                    if (File.Exists(logFile))
                    {
                        try
                        {
                            string[] lines = File.ReadAllLines(logFile);
                            int take = Math.Min(lines.Length, 12);
                            string[] tail = new string[take];
                            Array.Copy(lines, lines.Length - take, tail, 0, take);
                            details = "\n\nLog Çıktısı:\n" + string.Join("\n", tail).Trim();
                        }
                        catch { }
                    }
                }
                MessageBox.Show("G-Toolbox başlatılırken kapandı." + (string.IsNullOrEmpty(details) ? " Lütfen gereksinimleri kontrol edin." : details), "G-Toolbox Hata", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                this.Close();
                return;
            }

            string readyFile = Path.Combine(baseDir, ".gtoolbox_ready");
            bool isReady = false;
            if (File.Exists(readyFile))
            {
                try { File.Delete(readyFile); } catch { }
                isReady = true;
            }

            if (!isReady && checkCount > 4)
            {
                for (int port = 8000; port <= 8010; port++)
                {
                    try
                    {
                        HttpWebRequest req = (HttpWebRequest)WebRequest.Create("http://127.0.0.1:" + port + "/check-update");
                        req.Timeout = 200;
                        req.Method = "GET";
                        using (HttpWebResponse resp = (HttpWebResponse)req.GetResponse())
                        {
                            if (resp.StatusCode == HttpStatusCode.OK)
                            {
                                isReady = true;
                                break;
                            }
                        }
                    }
                    catch { }
                }
            }

            if (isReady)
            {
                lblStatus.Text = "Arayüz yükleniyor...";
                pollTimer.Stop();

                System.Windows.Forms.Timer closeTimer = new System.Windows.Forms.Timer();
                closeTimer.Interval = 750;
                closeTimer.Tick += (s, ev) =>
                {
                    closeTimer.Stop();
                    closeTimer.Dispose();
                    this.Close();
                };
                closeTimer.Start();
                return;
            }

            if (checkCount >= MaxChecks)
            {
                pollTimer.Stop();
                this.Close();
            }
        }
    }

    // ═════════════════════════════════════════════════════════════════════════
    // 3. MAIN PROGRAM ENTRY & RUNTIME DETECTOR
    // ═════════════════════════════════════════════════════════════════════════
    static class Program
    {
        [STAThread]
        static void Main(string[] args)
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);

            try
            {
                string baseDir = AppDomain.CurrentDomain.BaseDirectory;
                string script = Path.Combine(baseDir, "desktop_app.py");

                // Clean any leftover ready flag and old crash log
                string readyFile = Path.Combine(baseDir, ".gtoolbox_ready");
                if (File.Exists(readyFile))
                {
                    try { File.Delete(readyFile); } catch { }
                }
                string oldErr = Path.Combine(baseDir, "desktop_error.log");
                if (File.Exists(oldErr))
                {
                    try { File.Delete(oldErr); } catch { }
                }

                if (!File.Exists(script))
                {
                    MessageBox.Show("desktop_app.py bulunamadı:\n" + script, "G-Toolbox Hata", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    return;
                }

                // Check for valid Python environment
                string pythonExe = DetectWorkingPython(baseDir);

                // If no working environment is found, launch Setup Wizard!
                if (string.IsNullOrEmpty(pythonExe))
                {
                    using (SetupForm setup = new SetupForm(baseDir))
                    {
                        if (setup.ShowDialog() != DialogResult.OK)
                        {
                            // User cancelled setup
                            return;
                        }
                    }

                    // Re-detect python after setup
                    pythonExe = DetectWorkingPython(baseDir);
                    if (string.IsNullOrEmpty(pythonExe))
                    {
                        MessageBox.Show("Taşınabilir Python çalışma ortamı kurulamadı.", "G-Toolbox Hata", MessageBoxButtons.OK, MessageBoxIcon.Error);
                        return;
                    }
                }

                // Check if web mode requested
                bool webMode = false;
                foreach (string arg in args)
                {
                    if (arg == "--web" || arg == "-w") webMode = true;
                }

                ProcessStartInfo psi = new ProcessStartInfo();
                psi.FileName = pythonExe;
                if (webMode)
                {
                    psi.Arguments = "-m uvicorn main:app --host 0.0.0.0 --port 8000";
                }
                else
                {
                    psi.Arguments = "\"" + script + "\"";
                }
                psi.WorkingDirectory = baseDir;
                psi.UseShellExecute = false;
                psi.CreateNoWindow = true;
                psi.WindowStyle = ProcessWindowStyle.Hidden;

                Process pythonProc = Process.Start(psi);
                if (pythonProc == null)
                {
                    MessageBox.Show("G-Toolbox başlatılamadı. Python çalışma ortamını kontrol edin.", "G-Toolbox", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    return;
                }

                if (!webMode)
                {
                    RegisterStartMenuShortcut(baseDir);

                    SplashForm splash = new SplashForm(baseDir, pythonProc);
                    Application.Run(splash);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show("Başlatma hatası: " + ex.Message, "G-Toolbox", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private static string DetectWorkingPython(string baseDir)
        {
            // 1. Check embedded portable runtime
            string runtimePython = Path.Combine(baseDir, "runtime", "python.exe");
            if (File.Exists(runtimePython) && IsPythonReady(runtimePython))
            {
                return runtimePython;
            }

            // 2. Check virtual environment
            string venvPython = Path.Combine(baseDir, "venv", "Scripts", "python.exe");
            if (File.Exists(venvPython) && IsPythonReady(venvPython))
            {
                return venvPython;
            }

            // 3. Check system PATH python
            if (IsPythonReady("python.exe"))
            {
                return "python.exe";
            }

            return null;
        }

        private static bool IsPythonReady(string pyPath)
        {
            try
            {
                ProcessStartInfo psi = new ProcessStartInfo();
                psi.FileName = pyPath;
                psi.Arguments = "-c \"import uvicorn, fastapi, webview\"";
                psi.UseShellExecute = false;
                psi.CreateNoWindow = true;
                psi.WindowStyle = ProcessWindowStyle.Hidden;

                using (Process p = Process.Start(psi))
                {
                    if (p == null) return false;
                    p.WaitForExit(4000);
                    return p.HasExited && p.ExitCode == 0;
                }
            }
            catch
            {
                return false;
            }
        }

        private static void RegisterStartMenuShortcut(string baseDir)
        {
            try
            {
                string programsFolder = Environment.GetFolderPath(Environment.SpecialFolder.Programs);
                if (string.IsNullOrEmpty(programsFolder) || !Directory.Exists(programsFolder)) return;

                string shortcutPath = Path.Combine(programsFolder, "G-Toolbox.lnk");
                string exePath = Path.Combine(baseDir, "G-Toolbox.exe");
                if (!File.Exists(exePath)) exePath = Application.ExecutablePath;

                Type shellType = Type.GetTypeFromProgID("WScript.Shell");
                if (shellType == null) return;

                object shell = Activator.CreateInstance(shellType);
                object shortcut = shellType.InvokeMember("CreateShortcut",
                    System.Reflection.BindingFlags.InvokeMethod, null, shell, new object[] { shortcutPath });

                if (shortcut != null)
                {
                    Type scType = shortcut.GetType();
                    scType.InvokeMember("TargetPath", System.Reflection.BindingFlags.SetProperty, null, shortcut, new object[] { exePath });
                    scType.InvokeMember("WorkingDirectory", System.Reflection.BindingFlags.SetProperty, null, shortcut, new object[] { baseDir });
                    scType.InvokeMember("Description", System.Reflection.BindingFlags.SetProperty, null, shortcut, new object[] { "G-Toolbox — All-in-One Media & AI Studio" });

                    string ico = Path.Combine(baseDir, "static", "favicon.ico");
                    if (File.Exists(ico))
                    {
                        scType.InvokeMember("IconLocation", System.Reflection.BindingFlags.SetProperty, null, shortcut, new object[] { ico + ",0" });
                    }

                    scType.InvokeMember("Save", System.Reflection.BindingFlags.InvokeMethod, null, shortcut, null);
                }

                try
                {
                    using (Microsoft.Win32.RegistryKey key = Microsoft.Win32.Registry.CurrentUser.CreateSubKey(@"Software\Microsoft\Windows\CurrentVersion\App Paths\G-Toolbox.exe"))
                    {
                        if (key != null)
                        {
                            key.SetValue("", exePath);
                            key.SetValue("Path", baseDir);
                        }
                    }
                }
                catch { }
            }
            catch { }
        }
    }
}
