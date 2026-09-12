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
        self.assertIn("/api/system-status", route_paths)
        self.assertIn("/api/purge-vram", route_paths)
        self.assertIn("/burn-subtitles", route_paths)
        self.assertIn("/pdf-merge", route_paths)
        self.assertIn("/pdf-split", route_paths)
        self.assertIn("/pdf-extract-text", route_paths)
        self.assertIn("/audio-effects", route_paths)
        self.assertIn("/clean-audio-noise", route_paths)

    def test_system_status_and_purge_vram(self):
        """Verify /api/system-status and /api/purge-vram endpoints."""
        import asyncio
        from httpx import AsyncClient, ASGITransport

        async def _test():
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                res_status = await client.get("/api/system-status")
                self.assertEqual(res_status.status_code, 200)
                status_data = res_status.json()
                self.assertIn("cuda_available", status_data)
                self.assertIn("cpu_ram_total_mb", status_data)
                self.assertIn("models_cached", status_data)

                res_purge = await client.post("/api/purge-vram")
                self.assertEqual(res_purge.status_code, 200)
                purge_data = res_purge.json()
                self.assertTrue(purge_data["success"])
                self.assertIn("status", purge_data)

        asyncio.run(_test())

    def test_pdf_operations(self):
        """Verify PDF merge, split, and text extraction endpoints."""
        import asyncio
        from httpx import AsyncClient, ASGITransport
        from pypdf import PdfWriter, PdfReader

        # Create two 1-page PDF files in-memory
        def make_dummy_pdf(text_label):
            w = PdfWriter()
            w.add_blank_page(width=300, height=300)
            b = io.BytesIO()
            w.write(b)
            return b.getvalue()

        pdf1 = make_dummy_pdf("Page 1")
        pdf2 = make_dummy_pdf("Page 2")

        async def _test():
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                # 1. Merge
                files = [
                    ("files", ("doc1.pdf", pdf1, "application/pdf")),
                    ("files", ("doc2.pdf", pdf2, "application/pdf")),
                ]
                res_merge = await client.post("/pdf-merge", files=files)
                self.assertEqual(res_merge.status_code, 200)
                merged_bytes = res_merge.content
                reader = PdfReader(io.BytesIO(merged_bytes))
                self.assertEqual(len(reader.pages), 2)

                # 2. Split (extract page 1)
                files_split = {"file": ("merged.pdf", merged_bytes, "application/pdf")}
                res_split = await client.post("/pdf-split", files=files_split, data={"page_ranges": "1"})
                self.assertEqual(res_split.status_code, 200)
                split_reader = PdfReader(io.BytesIO(res_split.content))
                self.assertEqual(len(split_reader.pages), 1)

                # 3. Extract text
                res_text = await client.post("/pdf-extract-text", files=files_split)
                self.assertEqual(res_text.status_code, 200)
                text_data = res_text.json()
                self.assertTrue(text_data["success"])
                self.assertEqual(text_data["pages"], 2)

        asyncio.run(_test())

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

    def test_audio_effects_and_noise_cleaner(self):
        """Verify /audio-effects and /clean-audio-noise with a generated WAV."""
        import asyncio
        import wave
        import struct
        import math
        from httpx import AsyncClient, ASGITransport

        # Generate 0.2s synthetic audio (440Hz tone)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(44100)
            samples = [int(10000 * math.sin(2 * math.pi * 440 * i / 44100)) for i in range(8820)]
            wav_file.writeframes(struct.pack(f"<{len(samples)}h", *samples))
        wav_bytes = buf.getvalue()

        async def _test():
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                # 1. Test audio effects
                files = {"file": ("sine.wav", wav_bytes, "audio/wav")}
                res_fx = await client.post("/audio-effects", files=files, data={"preset": "slowed_reverb"})
                self.assertEqual(res_fx.status_code, 200)
                self.assertGreater(len(res_fx.content), 500)

                # 2. Test clean audio noise
                files_noise = {"file": ("sine.wav", wav_bytes, "audio/wav")}
                res_clean = await client.post("/clean-audio-noise", files=files_noise, data={"noise_preset": "light"})
                self.assertEqual(res_clean.status_code, 200)
                self.assertGreater(len(res_clean.content), 500)

        asyncio.run(_test())


if __name__ == "__main__":
    unittest.main()
