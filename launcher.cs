using System;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.IO;
using System.Net;
using System.Threading;
using System.Windows.Forms;

namespace GToolboxLauncher
{
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
            this.BackColor = Color.FromArgb(13, 17, 23); // Dark slate GitHub style

            // Try load icon
            string icoPath = Path.Combine(baseDir, "static", "favicon.ico");
            if (File.Exists(icoPath))
            {
                try
                {
                    this.Icon = new Icon(icoPath);
                }
                catch { }
            }

            // Custom Paint for border & subtle gradient
            this.Paint += (s, e) =>
            {
                Graphics g = e.Graphics;
                g.SmoothingMode = SmoothingMode.AntiAlias;

                // Subtle top gradient glow
                using (LinearGradientBrush brush = new LinearGradientBrush(
                    new Rectangle(0, 0, this.Width, 80),
                    Color.FromArgb(40, 99, 102, 241), // Indigo accent glow
                    Color.FromArgb(0, 13, 17, 23),
                    LinearGradientMode.Vertical))
                {
                    g.FillRectangle(brush, 0, 0, this.Width, 80);
                }

                // 1px Border
                using (Pen borderPen = new Pen(Color.FromArgb(99, 102, 241), 1.5f))
                {
                    g.DrawRectangle(borderPen, 0, 0, this.Width - 1, this.Height - 1);
                }
            };

            // Icon PictureBox
            picIcon = new PictureBox();
            picIcon.Size = new Size(54, 54);
            picIcon.Location = new Point(28, 30);
            picIcon.SizeMode = PictureBoxSizeMode.StretchImage;
            if (this.Icon != null)
            {
                picIcon.Image = this.Icon.ToBitmap();
            }
            this.Controls.Add(picIcon);

            // Title
            lblTitle = new Label();
            lblTitle.Text = "G-Toolbox";
            lblTitle.Font = new Font("Segoe UI", 19, FontStyle.Bold);
            lblTitle.ForeColor = Color.White;
            lblTitle.Location = new Point(94, 28);
            lblTitle.AutoSize = true;
            this.Controls.Add(lblTitle);

            // Subtitle
            lblSubtitle = new Label();
            lblSubtitle.Text = "All-in-One Media & AI Studio";
            lblSubtitle.Font = new Font("Segoe UI", 9.5f, FontStyle.Regular);
            lblSubtitle.ForeColor = Color.FromArgb(148, 163, 184); // Slate 400
            lblSubtitle.Location = new Point(96, 62);
            lblSubtitle.AutoSize = true;
            this.Controls.Add(lblSubtitle);

            // Status text
            lblStatus = new Label();
            lblStatus.Text = "Yapay zekâ ve medya motorları başlatılıyor...";
            lblStatus.Font = new Font("Segoe UI", 9.5f, FontStyle.Regular);
            lblStatus.ForeColor = Color.FromArgb(203, 213, 225); // Slate 300
            lblStatus.Location = new Point(30, 120);
            lblStatus.Size = new Size(400, 24);
            this.Controls.Add(lblStatus);

            // Modern Progress Bar
            progressBar = new ProgressBar();
            progressBar.Style = ProgressBarStyle.Marquee;
            progressBar.MarqueeAnimationSpeed = 25;
            progressBar.Location = new Point(30, 150);
            progressBar.Size = new Size(400, 7);
            this.Controls.Add(progressBar);

            // Version text
            lblVersion = new Label();
            lblVersion.Text = "v4.0.0 Desktop • Lütfen bekleyin...";
            lblVersion.Font = new Font("Segoe UI", 8.5f, FontStyle.Regular);
            lblVersion.ForeColor = Color.FromArgb(100, 116, 139); // Slate 500
            lblVersion.Location = new Point(30, 175);
            lblVersion.AutoSize = true;
            this.Controls.Add(lblVersion);

            // Polling timer
            pollTimer = new System.Windows.Forms.Timer();
            pollTimer.Interval = 250;
            pollTimer.Tick += PollTimer_Tick;
            pollTimer.Start();
        }

        private void PollTimer_Tick(object sender, EventArgs e)
        {
            checkCount++;

            // 1. Check if python crashed
            if (pythonProcess != null && pythonProcess.HasExited)
            {
                pollTimer.Stop();
                MessageBox.Show("G-Toolbox başlatılırken kapandı. Lütfen gereksinimleri kontrol edin.", "G-Toolbox Hata", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                this.Close();
                return;
            }

            // 2. Check if ready file exists
            string readyFile = Path.Combine(baseDir, ".gtoolbox_ready");
            bool isReady = false;
            if (File.Exists(readyFile))
            {
                try { File.Delete(readyFile); } catch { }
                isReady = true;
            }

            // 3. Fallback: HTTP check on ports 8000..8010
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

                // Short delay to allow WebView window to smoothly show
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
                // Timeout exceeded, close splash anyway so user isn't stuck
                pollTimer.Stop();
                this.Close();
            }
        }
    }

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
                string venvPython = Path.Combine(baseDir, "venv", "Scripts", "python.exe");
                string pythonExe = File.Exists(venvPython) ? venvPython : "python.exe";
                string script = Path.Combine(baseDir, "desktop_app.py");

                // Clean any leftover ready flag
                string readyFile = Path.Combine(baseDir, ".gtoolbox_ready");
                if (File.Exists(readyFile))
                {
                    try { File.Delete(readyFile); } catch { }
                }

                if (!File.Exists(script))
                {
                    MessageBox.Show("desktop_app.py bulunamadı:\n" + script, "G-Toolbox Hata", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    return;
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
                    MessageBox.Show("G-Toolbox başlatılamadı. Python'un kurulu olduğundan emin olun.", "G-Toolbox", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    return;
                }

                if (!webMode)
                {
                    // Launch Splash Screen immediately
                    SplashForm splash = new SplashForm(baseDir, pythonProc);
                    Application.Run(splash);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show("Başlatma hatası: " + ex.Message, "G-Toolbox", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }
    }
}
