import io
import sys
import unittest
from pathlib import Path
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import main
from main import app, format_timestamp


class TestNewFeatures(unittest.TestCase):
    def test_format_timestamp(self):
        """Verify SRT timestamp formatting."""
        self.assertEqual(format_timestamp(0.0), "00:00:00,000")
        self.assertEqual(format_timestamp(65.5), "00:01:05,500")
        self.assertEqual(format_timestamp(3661.123), "01:01:01,123")

    def test_exif_metadata_view_and_strip(self):
        """Create an image with EXIF and verify view and strip endpoints."""
        import asyncio
        from httpx import AsyncClient, ASGITransport

        # Create dummy JPEG with EXIF
        img = Image.new("RGB", (100, 100), color="blue")
        exif = img.getexif()
        exif[0x010E] = "G-Toolbox Test Image Description"
        exif[0x010F] = "TestCameraMake"
        
        buf = io.BytesIO()
        img.save(buf, format="JPEG", exif=exif)
        img_bytes = buf.getvalue()

        async def _test():
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                # Test /view-metadata
                files = {"file": ("test_exif.jpg", img_bytes, "image/jpeg")}
                res_view = await client.post("/view-metadata", files=files)
                self.assertEqual(res_view.status_code, 200)
                data = res_view.json()
                self.assertIn("tags", data)
                self.assertGreaterEqual(data["tag_count"], 1)

                # Test /strip-metadata
                files = {"file": ("test_exif.jpg", img_bytes, "image/jpeg")}
                res_strip = await client.post("/strip-metadata", files=files)
                self.assertEqual(res_strip.status_code, 200)
                clean_bytes = res_strip.content
                clean_img = Image.open(io.BytesIO(clean_bytes))
                clean_exif = clean_img.getexif()
                self.assertEqual(len(clean_exif), 0)

        asyncio.run(_test())

    def test_routes_declared(self):
        """Verify that all new endpoints are registered on the FastAPI app."""
        route_paths = [route.path for route in app.routes]
        self.assertIn("/separate-audio", route_paths)
        self.assertIn("/transcribe-media", route_paths)
        self.assertIn("/view-metadata", route_paths)
        self.assertIn("/strip-metadata", route_paths)
        self.assertIn("/video-to-anim", route_paths)
        self.assertIn("/convert-universal", route_paths)

    def test_convert_universal_endpoint(self):
        """Verify that /convert-universal converts an image properly without src_path NameError."""
        import asyncio
        from httpx import AsyncClient, ASGITransport

        img = Image.new("RGB", (64, 64), color="red")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        png_bytes = buf.getvalue()

        async def _test():
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                files = {"file": ("test_image.png", png_bytes, "image/png")}
                data = {"target_format": "webp"}
                res = await client.post("/convert-universal", files=files, data=data)
                self.assertEqual(res.status_code, 200)
                out_img = Image.open(io.BytesIO(res.content))
                self.assertEqual(out_img.format, "WEBP")
                self.assertEqual(out_img.size, (64, 64))

        asyncio.run(_test())

    def test_ffmpeg_path_registration(self):
        """Verify that FFMPEG_DIR is automatically injected into os.environ PATH."""
        import os
        if main.FFMPEG_DIR:
            self.assertIn(main.FFMPEG_DIR, os.environ.get("PATH", ""))


if __name__ == "__main__":
    unittest.main()
