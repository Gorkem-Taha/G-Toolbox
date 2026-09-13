using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

namespace GToolboxLauncher
{
    static class Program
    {
        [STAThread]
        static void Main(string[] args)
        {
            try
            {
                string baseDir = AppDomain.CurrentDomain.BaseDirectory;
                string venvPython = Path.Combine(baseDir, "venv", "Scripts", "python.exe");
                string pythonExe = File.Exists(venvPython) ? venvPython : "python.exe";
                string script = Path.Combine(baseDir, "desktop_app.py");

                if (!File.Exists(script))
                {
                    MessageBox.Show("desktop_app.py bulunamadı:\n" + script, "G-Toolbox Hata", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    return;
                }

                // Check if web mode requested via argument or default to desktop app
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

                Process p = Process.Start(psi);
                if (p == null)
                {
                    MessageBox.Show("G-Toolbox başlatılamadı. Python'un kurulu olduğundan emin olun.", "G-Toolbox", MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show("Başlatma hatası: " + ex.Message, "G-Toolbox", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }
    }
}
