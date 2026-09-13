import sys
import unittest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import desktop_app


class TestDesktopApp(unittest.TestCase):
    def test_port_finder(self):
        """Verify that find_available_port returns a valid integer port."""
        port = desktop_app.find_available_port(start_port=9123)
        self.assertIsInstance(port, int)
        self.assertGreaterEqual(port, 9123)

    def test_server_thread_init(self):
        """Verify that ServerThread can be constructed with FastAPI app."""
        from main import app
        thread = desktop_app.ServerThread(app, host="127.0.0.1", port=9124)
        self.assertTrue(thread.daemon)
        self.assertIsNotNone(thread.server)

    def test_wait_for_server_timeout(self):
        """Verify that wait_for_server returns False when polling an inactive port within brief timeout."""
        result = desktop_app.wait_for_server("http://127.0.0.1:59999", timeout=0.3)
        self.assertFalse(result)

    def test_lan_ip_detection(self):
        """Verify that get_lan_ip returns a valid IPv4 string."""
        from main import get_lan_ip
        ip = get_lan_ip()
        self.assertIsInstance(ip, str)
        parts = ip.split(".")
        self.assertEqual(len(parts), 4)

    def test_network_info_route(self):
        """Verify that /api/network-info returns 200 with valid keys."""
        import asyncio
        from httpx import AsyncClient, ASGITransport
        from main import app

        async def _test():
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                res = await client.get("/api/network-info")
                self.assertEqual(res.status_code, 200)
                data = res.json()
                self.assertIn("lan_ip", data)
                self.assertIn("mobile_url", data)

    def test_executable_exists(self):
        """Verify that G-Toolbox.exe launcher exists in project root."""
        exe_path = PROJECT_ROOT / "G-Toolbox.exe"
        self.assertTrue(exe_path.exists())
        self.assertGreater(exe_path.stat().st_size, 1000)

    def test_i18n_integrity(self):
        """Verify that all data-i18n tags in index.html exist in translations dictionary in app.js."""
        import re
        html = (PROJECT_ROOT / "templates" / "index.html").read_text(encoding="utf-8")
        js = (PROJECT_ROOT / "static" / "js" / "app.js").read_text(encoding="utf-8")

        html_keys = set(re.findall(r'data-i18n=["\']([^"\']+)["\']', html))
        self.assertGreater(len(html_keys), 50)

        # Ensure both en and tr contain the keys
        en_match = re.search(r'en:\s*\{(.*?)\},\s*tr:', js, re.DOTALL)
        tr_match = re.search(r'tr:\s*\{(.*?)\}\s*\n\s*\};', js, re.DOTALL)

        self.assertIsNotNone(en_match)
        self.assertIsNotNone(tr_match)

        en_keys = set(re.findall(r'["\']?([a-zA-Z0-9_\-]+)["\']?\s*:', en_match.group(1)))
        tr_keys = set(re.findall(r'["\']?([a-zA-Z0-9_\-]+)["\']?\s*:', tr_match.group(1)))

        missing_en = html_keys - en_keys
        missing_tr = html_keys - tr_keys

        self.assertEqual(missing_en, set(), f"Missing EN keys: {missing_en}")
        self.assertEqual(missing_tr, set(), f"Missing TR keys: {missing_tr}")

    def test_ytdlp_multi_client_opts(self):
        """Verify that _build_ytdlp_opts sets up anti-403 multi-client routing."""
        from main import _build_ytdlp_opts
        opts = _build_ytdlp_opts()
        self.assertIn("extractor_args", opts)
        self.assertIn("youtube", opts["extractor_args"])
        self.assertIn("player_client", opts["extractor_args"]["youtube"])
        clients = opts["extractor_args"]["youtube"]["player_client"]
        self.assertIn("android", clients)
        self.assertIn("ios", clients)
        self.assertTrue(opts.get("nocheckcertificate"))

    def test_save_endpoints_exist(self):
        """Verify that /api/save-task-file and /api/save-blob-file routes are registered."""
        from main import app
        route_paths = [r.path for r in app.routes]
        self.assertIn("/api/save-task-file", route_paths)
        self.assertIn("/api/save-blob-file", route_paths)

    def test_ai_status_endpoint(self):
        """Verify that /api/ai-status returns 200 with model keys."""
        from main import app, check_ai_models_status
        status = check_ai_models_status()
        self.assertIn("models", status)
        self.assertIn("realesrgan_general", status["models"])
        self.assertIn("lama", status["models"])
        self.assertIn("u2net", status["models"])

        route_paths = [r.path for r in app.routes]
        self.assertIn("/api/ai-status", route_paths)
        self.assertIn("/api/install-ai-models", route_paths)
        self.assertIn("/api/delete-ai-models", route_paths)

    def test_delete_ai_models_execution(self):
        """Verify that delete_ai_models executes and returns JSON response with freed_mb."""
        import asyncio
        from httpx import AsyncClient, ASGITransport
        from main import app

        async def _test():
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                res = await client.post("/api/delete-ai-models")
                self.assertEqual(res.status_code, 200)
                data = res.json()
                self.assertTrue(data.get("success"))
                self.assertIn("freed_mb", data)
                self.assertIn("message", data)
        asyncio.run(_test())

    def test_ready_flag_lifecycle(self):
        """Verify ready flag file creation and cleanup in desktop_app."""
        desktop_app.notify_ready()
        ready_file = PROJECT_ROOT / ".gtoolbox_ready"
        self.assertTrue(ready_file.exists())
        desktop_app.cleanup_ready_flag()
        self.assertFalse(ready_file.exists())

    def test_appimage_assets_exist(self):
        """Verify that Linux AppImage packaging assets exist."""
        script = PROJECT_ROOT / "scripts" / "build_appimage.sh"
        workflow = PROJECT_ROOT / ".github" / "workflows" / "build-appimage.yml"
        desktop_entry = PROJECT_ROOT / "g-toolbox.desktop"
        icon_png = PROJECT_ROOT / "static" / "icon.png"

        self.assertTrue(script.exists())
        self.assertTrue(workflow.exists())
        self.assertTrue(desktop_entry.exists())
        self.assertTrue(icon_png.exists())


if __name__ == "__main__":
    unittest.main()


