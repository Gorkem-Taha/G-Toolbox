using System;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.IO;
using System.IO.Compression;
using System.Net;
using System.Runtime.InteropServices;
using System.Security.Principal;
using System.Threading;
using System.Windows.Forms;

namespace GToolboxLauncher
{
    // ═════════════════════════════════════════════════════════════════════════
    // 0. SYSTEM & SECURITY HELPERS (Admin Elevation, Zone.Identifier, VC++ Redist)
    // ═════════════════════════════════════════════════════════════════════════
    internal static class SecurityHelper
    {
        [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool DeleteFile(string name);

        public static bool IsAdministrator()
        {
            try
            {
                WindowsIdentity identity = WindowsIdentity.GetCurrent();
                WindowsPrincipal principal = new WindowsPrincipal(identity);
                return principal.IsInRole(WindowsBuiltInRole.Administrator);
            }
            catch
            {
                return false;
            }
        }

        public static bool RestartAsAdministrator(string[] args)
        {
            try
            {
                ProcessStartInfo psi = new ProcessStartInfo();
                psi.FileName = Application.ExecutablePath;
                if (args != null && args.Length > 0)
                {
                    psi.Arguments = string.Join(" ", args);
                }
                psi.Verb = "runas";
                psi.UseShellExecute = true;
                Process.Start(psi);
                return true;
            }
            catch
            {
                return false;
            }
        }

        public static void UnblockDirectory(string dirPath)
        {
            try
            {
                if (string.IsNullOrEmpty(dirPath) || !Directory.Exists(dirPath)) return;

                string[] files = Directory.GetFiles(dirPath, "*.*", SearchOption.AllDirectories);
                foreach (string file in files)
                {
                    try
                    {
                        DeleteFile(file + ":Zone.Identifier");
                    }
                    catch { }
                }
            }
            catch { }
        }

        public static bool IsVcRedistInstalled()
        {
            try
            {
                string sysDir = Environment.GetFolderPath(Environment.SpecialFolder.System);
                string vc140_1 = Path.Combine(sysDir, "vcruntime140_1.dll");
                string msvcp140 = Path.Combine(sysDir, "msvcp140.dll");

                if (File.Exists(vc140_1) && File.Exists(msvcp140))
                {
                    return true;
                }

                using (Microsoft.Win32.RegistryKey key = Microsoft.Win32.Registry.LocalMachine.OpenSubKey(@"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\X64"))
                {
                    if (key != null)
                    {
                        object val = key.GetValue("Installed");
                        if (val != null && Convert.ToInt32(val) == 1)
                        {
                            return true;
                        }
                    }
                }
            }
            catch { }

            return false;
        }

        public static void AddDefenderExclusion(string folderPath)
        {
            if (!IsAdministrator() || string.IsNullOrEmpty(folderPath) || !Directory.Exists(folderPath)) return;
            try
            {
                ProcessStartInfo psi = new ProcessStartInfo();
                psi.FileName = "powershell.exe";
                psi.Arguments = "-NoProfile -ExecutionPolicy Bypass -Command \"Add-MpPreference -ExclusionPath '" + folderPath.Replace("'", "''") + "' -ErrorAction SilentlyContinue\"";
                psi.UseShellExecute = false;
                psi.CreateNoWindow = true;
                psi.WindowStyle = ProcessWindowStyle.Hidden;

                using (Process p = Process.Start(psi))
                {
                    if (p != null) p.WaitForExit(5000);
                }
            }
            catch { }
        }
    }

    // ═════════════════════════════════════════════════════════════════════════
    // 1. ICON & ASSET HELPER (Crisp, High-Resolution Icon Loader)
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
    // 2. SETUP / DOWNLOAD WIZARD FORM (Portable Python 3.10 & Runtime Engine)
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
        private bool isInstalling = false;
        private string baseDir;

        public SetupForm(string directory)
        {
            this.baseDir = directory;
            InitUI();
        }

        private void InitUI()
        {
            this.Size = new Size(540, 320);
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

            // Subtitle (English)
            lblSubtitle = new Label();
            lblSubtitle.Text = "Zero-Config Setup: Portable Python 3.10 & Core Engine";
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
            lblClose.Location = new Point(505, 12);
            lblClose.Size = new Size(24, 24);
            lblClose.Cursor = Cursors.Hand;
            lblClose.Click += (s, e) => { if (!isInstalling) { this.DialogResult = DialogResult.Cancel; this.Close(); } };
            this.Controls.Add(lblClose);

            // Status text (English)
            lblStatus = new Label();
            lblStatus.Text = "Python environment not found. Downloading portable runtime...";
            lblStatus.Font = new Font("Segoe UI", 9.5f, FontStyle.Bold);
            lblStatus.ForeColor = Color.FromArgb(203, 213, 225);
            lblStatus.Location = new Point(30, 102);
            lblStatus.Size = new Size(480, 22);
            this.Controls.Add(lblStatus);

            // Detail text (English)
            lblDetail = new Label();
            lblDetail.Text = "Your system remains clean. The application will launch automatically when ready.";
            lblDetail.Font = new Font("Segoe UI", 8.5f, FontStyle.Regular);
            lblDetail.ForeColor = Color.FromArgb(148, 163, 184);
            lblDetail.Location = new Point(30, 126);
            lblDetail.Size = new Size(480, 20);
            this.Controls.Add(lblDetail);

            // Progress Bar
            progressBar = new ProgressBar();
            progressBar.Location = new Point(30, 154);
            progressBar.Size = new Size(480, 10);
            progressBar.Style = ProgressBarStyle.Continuous;
            this.Controls.Add(progressBar);

            // AI Checkbox (English)
            chkInstallAi = new CheckBox();
            chkInstallAi.Text = "Download AI Engine now (PyTorch CPU, Real-ESRGAN, LaMa, U2-Net ~250MB)";
            chkInstallAi.Font = new Font("Segoe UI", 8.5f, FontStyle.Regular);
            chkInstallAi.ForeColor = Color.FromArgb(203, 213, 225);
            chkInstallAi.Location = new Point(30, 180);
            chkInstallAi.Size = new Size(480, 24);
            chkInstallAi.Checked = false;
            this.Controls.Add(chkInstallAi);

            // Start Button (English)
            btnStart = new Button();
            btnStart.Text = "Start Installation";
            btnStart.Font = new Font("Segoe UI", 9.5f, FontStyle.Bold);
            btnStart.ForeColor = Color.White;
            btnStart.BackColor = Color.FromArgb(99, 102, 241);
            btnStart.FlatStyle = FlatStyle.Flat;
            btnStart.FlatAppearance.BorderSize = 0;
            btnStart.Location = new Point(30, 216);
            btnStart.Size = new Size(480, 36);
            btnStart.Cursor = Cursors.Hand;
            btnStart.Click += (s, e) =>
            {
                StartInstallation();
            };
            this.Controls.Add(btnStart);

            // Version info footer (English)
            Label lblVer = new Label();
            lblVer.Text = "G-Toolbox v4.4 • Zero Dependencies & Portable Environment" + (SecurityHelper.IsAdministrator() ? " (Administrator)" : "");
            lblVer.Font = new Font("Segoe UI", 8f, FontStyle.Regular);
            lblVer.ForeColor = Color.FromArgb(100, 116, 139);
            lblVer.Location = new Point(30, 268);
            lblVer.AutoSize = true;
            this.Controls.Add(lblVer);
        }

        private void StartInstallation()
        {
            if (isInstalling) return;
            isInstalling = true;

            // Hide buttons and options when download begins
            btnStart.Visible = false;
            chkInstallAi.Visible = false;
            lblClose.Visible = false;

            progressBar.Size = new Size(480, 14);
            progressBar.Style = ProgressBarStyle.Continuous;
            progressBar.Value = 0;

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
                try
                {
                    ServicePointManager.ServerCertificateValidationCallback = delegate { return true; };
                }
                catch { }

                // ── STEP 1: Download Python 3.10.11 Embeddable ZIP ───────
                UpdateUI("1/5: Downloading Portable Python 3.10.11...", "Fetching official package from python.org (~8.2 MB)...", 0, ProgressBarStyle.Continuous);

                string pyUrl = "https://www.python.org/ftp/python/3.10.11/python-3.10.11-embed-amd64.zip";
                DownloadFileWithProgress(pyUrl, zipPath, "1/5: Downloading Portable Python 3.10.11...", 8.2);

                // ── STEP 2: Extract to runtime/ ──────────────────────────
                UpdateUI("2/5: Extracting runtime environment to runtime/...", "Please wait, extracting files...", 0, ProgressBarStyle.Marquee);

                if (Directory.Exists(runtimeDir))
                {
                    try { Directory.Delete(runtimeDir, true); } catch { }
                }
                Directory.CreateDirectory(runtimeDir);

                ZipFile.ExtractToDirectory(zipPath, runtimeDir);
                try { File.Delete(zipPath); } catch { }

                // ── STEP 3: Configure python310._pth & Pip ───────────────
                UpdateUI("3/5: Configuring package paths and Pip...", "Enabling site packages in python310._pth...", 0, ProgressBarStyle.Marquee);

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
                UpdateUI("3/5: Downloading Pip package manager...", "Fetching get-pip.py from bootstrap.pypa.io...", 0, ProgressBarStyle.Marquee);
                DownloadFileWithProgress("https://bootstrap.pypa.io/get-pip.py", getPipPath, "3/5: Downloading Pip package manager...", 2.5);

                string pythonExe = Path.Combine(runtimeDir, "python.exe");
                UpdateUI("3/5: Installing Pip...", "Installing pip and setuptools into runtime...", 0, ProgressBarStyle.Marquee);
                RunProcess(pythonExe, "\"" + getPipPath + "\" --no-warn-script-location --default-timeout 180 --trusted-host pypi.org --trusted-host files.pythonhosted.org", runtimeDir);
                try { File.Delete(getPipPath); } catch { }

                // ── STEP 4: System Dependencies & Security Policies ──────
                UpdateUI("4/5: Checking system dependencies (Visual C++ Redist)...", "Verifying Microsoft Visual C++ 2015-2022 Redistributable...", 0, ProgressBarStyle.Marquee);

                if (!SecurityHelper.IsVcRedistInstalled())
                {
                    UpdateUI("4/5: Installing Microsoft Visual C++ Redistributable...", "Downloading and installing official vc_redist.x64.exe...", 0, ProgressBarStyle.Marquee);
                    string vcRedistPath = Path.Combine(Path.GetTempPath(), "vc_redist.x64.exe");
                    try
                    {
                        DownloadFileWithProgress("https://aka.ms/vs/17/release/vc_redist.x64.exe", vcRedistPath, "4/5: Installing Microsoft Visual C++ Redistributable...", 24.0);
                        ProcessStartInfo psiVc = new ProcessStartInfo();
                        psiVc.FileName = vcRedistPath;
                        psiVc.Arguments = "/install /quiet /norestart";
                        psiVc.UseShellExecute = true;
                        if (!SecurityHelper.IsAdministrator())
                        {
                            psiVc.Verb = "runas";
                        }
                        using (Process pVc = Process.Start(psiVc))
                        {
                            if (pVc != null) pVc.WaitForExit(180000);
                        }
                    }
                    catch { }
                    finally
                    {
                        try { if (File.Exists(vcRedistPath)) File.Delete(vcRedistPath); } catch { }
                    }
                }

                // Remove Zone.Identifier from base directory and runtime
                UpdateUI("4/5: Unblocking files & applying security policies...", "Removing Mark-of-the-Web (Zone.Identifier)...", 0, ProgressBarStyle.Marquee);
                SecurityHelper.UnblockDirectory(baseDir);
                if (SecurityHelper.IsAdministrator())
                {
                    SecurityHelper.AddDefenderExclusion(baseDir);
                }

                // ── STEP 5: Install Core Dependencies ───────────────────
                UpdateUI("5/5: Installing core engine packages...", "FastAPI, WebView, Media Tools and dependencies (1-2 min)...", 0, ProgressBarStyle.Marquee);

                string corePackages = "fastapi uvicorn python-multipart jinja2 pydantic ffmpeg-python yt-dlp Pillow pyAesCrypt pypdf pywebview opencv-python numpy aiofiles psutil certifi --no-warn-script-location --prefer-binary --default-timeout 180 --retries 5 --trusted-host pypi.org --trusted-host files.pythonhosted.org";
                RunProcess(pythonExe, "-m pip install " + corePackages, runtimeDir);

                if (installAi)
                {
                    UpdateUI("5/5+: Installing AI Engine (PyTorch CPU)...", "Downloading PyTorch CPU packages (~250 MB)...", 0, ProgressBarStyle.Marquee);
                    RunProcess(pythonExe, "-m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu --no-warn-script-location --prefer-binary --default-timeout 180 --retries 5 --trusted-host download.pytorch.org --trusted-host pypi.org --trusted-host files.pythonhosted.org", runtimeDir);
                    UpdateUI("5/5+: Configuring BasicSR architecture...", "Installing BasicSR components...", 0, ProgressBarStyle.Marquee);
                    RunProcess(pythonExe, "-m pip install basicsr --no-deps --no-warn-script-location --prefer-binary --default-timeout 180 --trusted-host pypi.org --trusted-host files.pythonhosted.org", runtimeDir);
                    UpdateUI("5/5+: Installing AI modules...", "Installing RealESRGAN, Rembg, LaMa, Whisper, Demucs...", 0, ProgressBarStyle.Marquee);
                    RunProcess(pythonExe, "-m pip install realesrgan rembg simple-lama-inpainting faster-whisper demucs --no-warn-script-location --prefer-binary --default-timeout 180 --retries 5 --trusted-host pypi.org --trusted-host files.pythonhosted.org", runtimeDir);

                    // Ensure PyTorch DLLs are completely unblocked
                    string torchLib = Path.Combine(runtimeDir, "Lib", "site-packages", "torch", "lib");
                    if (Directory.Exists(torchLib))
                    {
                        SecurityHelper.UnblockDirectory(torchLib);
                    }
                }

                // ── STEP 6: Finished! ───────────────────────────────────
                UpdateUI("🎉 Installation complete!", "Launching G-Toolbox...", 100, ProgressBarStyle.Continuous);
                Thread.Sleep(1200);

                try
                {
                    this.BeginInvoke((MethodInvoker)delegate
                    {
                        this.DialogResult = DialogResult.OK;
                        this.Close();
                    });
                }
                catch { }
            }
            catch (Exception ex)
            {
                try
                {
                    this.BeginInvoke((MethodInvoker)delegate
                    {
                        string errText = ex.Message;
                        bool isPolicyError = errText.Contains("4551") || errText.Contains("c10.dll") || errText.ToLower().Contains("application control") || errText.ToLower().Contains("uygulama denetimi");

                        string msg = "An error occurred during installation:\n\n" + errText;
                        if (isPolicyError || !SecurityHelper.IsAdministrator())
                        {
                            msg += "\n\nThis may be caused by Windows security policies or missing permissions.\nWould you like to restart G-Toolbox as Administrator to resolve this?";
                            DialogResult dr = MessageBox.Show(msg, "G-Toolbox Setup Error", MessageBoxButtons.YesNo, MessageBoxIcon.Error);
                            if (dr == DialogResult.Yes)
                            {
                                SecurityHelper.RestartAsAdministrator(null);
                                this.DialogResult = DialogResult.Cancel;
                                this.Close();
                                return;
                            }
                        }
                        else
                        {
                            msg += "\n\nPlease check your internet connection and try again.";
                            MessageBox.Show(msg, "G-Toolbox Setup Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                        }

                        isInstalling = false;
                        btnStart.Visible = true;
                        btnStart.Enabled = true;
                        btnStart.Text = "Retry";
                        chkInstallAi.Visible = true;
                        chkInstallAi.Enabled = true;
                        lblClose.Visible = true;
                        lblStatus.Text = "Installation could not be completed.";
                        lblDetail.Text = "Error: " + ex.Message;
                        progressBar.Style = ProgressBarStyle.Continuous;
                        progressBar.Value = 0;
                    });
                }
                catch { }
            }
        }

        private void DownloadFileWithProgress(string url, string destPath, string stepLabel, double expectedMb)
        {
            string parent = Path.GetDirectoryName(destPath);
            if (!string.IsNullOrEmpty(parent) && !Directory.Exists(parent))
            {
                Directory.CreateDirectory(parent);
            }

            if (File.Exists(destPath))
            {
                try { File.Delete(destPath); } catch { }
            }

            HttpWebRequest request = (HttpWebRequest)WebRequest.Create(url);
            request.Proxy = null; // Bypasses 15-30s WPAD proxy delay on Windows
            request.Timeout = 180000;
            request.ReadWriteTimeout = 180000;
            request.UserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) G-Toolbox/4.4";
            request.KeepAlive = true;
            request.AutomaticDecompression = DecompressionMethods.GZip | DecompressionMethods.Deflate;

            using (HttpWebResponse response = (HttpWebResponse)request.GetResponse())
            {
                long totalBytes = response.ContentLength;
                double totalMb = totalBytes > 0 ? totalBytes / 1048576.0 : expectedMb;

                using (Stream responseStream = response.GetResponseStream())
                using (FileStream fileStream = new FileStream(destPath, FileMode.Create, FileAccess.Write, FileShare.None, 65536))
                {
                    byte[] buffer = new byte[65536];
                    long totalRead = 0;
                    int bytesRead;
                    long lastUiUpdate = 0;

                    while ((bytesRead = responseStream.Read(buffer, 0, buffer.Length)) > 0)
                    {
                        fileStream.Write(buffer, 0, bytesRead);
                        totalRead += bytesRead;

                        long now = Environment.TickCount;
                        if (now - lastUiUpdate > 60 || (totalBytes > 0 && totalRead == totalBytes))
                        {
                            lastUiUpdate = now;
                            double receivedMb = totalRead / 1048576.0;
                            int pct = totalBytes > 0 ? (int)((totalRead * 100) / totalBytes) : -1;
                            string detail = string.Format("Downloaded: {0:F1} MB / {1:F1} MB{2}",
                                receivedMb,
                                totalMb,
                                pct >= 0 ? string.Format(" ({0}%)", pct) : "");

                            UpdateUI(stepLabel, detail, pct >= 0 ? pct : 0, pct >= 0 ? ProgressBarStyle.Continuous : ProgressBarStyle.Marquee);
                        }
                    }
                    fileStream.Flush();
                }
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
                    throw new Exception("Operation timed out (15 min): " + exe);
                }

                string stderr = errBuffer.ToString();
                if (p.ExitCode != 0 && !string.IsNullOrEmpty(stderr) && (stderr.Contains("ERROR:") || stderr.Contains("Traceback") || stderr.Contains("Fatal error:")))
                {
                    throw new Exception("Process error (code " + p.ExitCode + "):\n" + stderr);
                }
            }
        }

        private void UpdateUI(string status, string detail, int progress, ProgressBarStyle style)
        {
            if (this.IsDisposed) return;
            try
            {
                if (!this.IsHandleCreated) return;
                this.BeginInvoke((MethodInvoker)delegate
                {
                    if (this.IsDisposed) return;
                    if (status != null) lblStatus.Text = status;
                    if (detail != null) lblDetail.Text = detail;
                    if (progressBar.Style != style) progressBar.Style = style;
                    if (style == ProgressBarStyle.Continuous)
                    {
                        if (progress >= 0 && progress <= 100) progressBar.Value = progress;
                    }
                });
            }
            catch { }
        }
    }

    // ═════════════════════════════════════════════════════════════════════════
    // 3. SPLASH SCREEN FORM (Fast Startup & Readiness Poller)
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
            lblStatus.Text = "Starting AI and media engines...";
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
            lblVersion.Text = "v4.4 Desktop • Please wait...";
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
                    try { details = "\n\nError Details:\n" + File.ReadAllText(errFile).Trim(); } catch { }
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
                            details = "\n\nLog Output:\n" + string.Join("\n", tail).Trim();
                        }
                        catch { }
                    }
                }

                bool isPolicyBlocked = details.Contains("4551") || details.Contains("c10.dll") || details.ToLower().Contains("application control") || details.ToLower().Contains("uygulama denetimi");
                if (isPolicyBlocked && !SecurityHelper.IsAdministrator())
                {
                    DialogResult dr = MessageBox.Show("G-Toolbox was blocked by Windows Application Control policies (Smart App Control / c10.dll).\n\nWould you like to restart G-Toolbox as Administrator to resolve this?" + details, "G-Toolbox Security Policy Block", MessageBoxButtons.YesNo, MessageBoxIcon.Warning);
                    if (dr == DialogResult.Yes)
                    {
                        SecurityHelper.RestartAsAdministrator(null);
                    }
                }
                else
                {
                    MessageBox.Show("G-Toolbox closed unexpectedly." + (string.IsNullOrEmpty(details) ? " Please check requirements or run as Administrator." : details), "G-Toolbox Error", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                }

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
                lblStatus.Text = "Loading interface...";
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
    // 4. MAIN PROGRAM ENTRY & RUNTIME DETECTOR
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

                // Automatically unblock all files in base directory to strip Zone.Identifier
                SecurityHelper.UnblockDirectory(baseDir);

                if (!File.Exists(script))
                {
                    MessageBox.Show("desktop_app.py was not found:\n" + script, "G-Toolbox Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    return;
                }

                // Check for valid Python environment
                string pythonExe = DetectWorkingPython(baseDir);

                // If setup is needed OR Visual C++ Redistributable is missing, recommend Administrator privileges with user confirmation
                if (!SecurityHelper.IsAdministrator())
                {
                    bool needsSetup = string.IsNullOrEmpty(pythonExe);
                    bool needsVcRedist = !SecurityHelper.IsVcRedistInstalled();

                    if (needsSetup || needsVcRedist)
                    {
                        DialogResult prompt = MessageBox.Show(
                            "G-Toolbox requires Administrator privileges to install system runtime components (Microsoft Visual C++ Redistributable) and configure Windows security policies.\n\nWould you like to run G-Toolbox as Administrator?",
                            "G-Toolbox - Administrator Privileges Recommended",
                            MessageBoxButtons.YesNo,
                            MessageBoxIcon.Question);

                        if (prompt == DialogResult.Yes)
                        {
                            if (SecurityHelper.RestartAsAdministrator(args))
                            {
                                return; // Exit non-admin instance; elevated instance is starting
                            }
                        }
                    }
                }

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
                        MessageBox.Show("Portable Python runtime could not be installed.", "G-Toolbox Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
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
                    MessageBox.Show("G-Toolbox could not be started. Check Python runtime environment.", "G-Toolbox", MessageBoxButtons.OK, MessageBoxIcon.Error);
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
                MessageBox.Show("Startup error: " + ex.Message, "G-Toolbox", MessageBoxButtons.OK, MessageBoxIcon.Error);
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
