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

        asyncio.run(_test())


if __name__ == "__main__":
    unittest.main()
