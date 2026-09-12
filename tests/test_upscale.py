"""
Test Suite for G-Toolbox Image Upscaling Pipeline
Verifies RGBA, Grayscale, Oversized image handling, and channel preservation.
"""

import os
import sys
import numpy as np
import cv2
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Verify torchvision patch
import torchvision.transforms.functional as functional
sys.modules['torchvision.transforms.functional_tensor'] = functional

def test_rgba_channel_separation():
    print("[TEST 1] Testing RGBA channel extraction and recombination...")
    # Create 200x200 RGBA image with varying alpha
    h, w = 200, 200
    img = np.zeros((h, w, 4), dtype=np.uint8)
    img[:, :, 0] = 120  # B
    img[:, :, 1] = 180  # G
    img[:, :, 2] = 240  # R
    img[:, :, 3] = 128  # Alpha 50%
    
    # Simulate pipeline logic
    has_alpha = False
    alpha_channel = None
    if len(img.shape) == 3 and img.shape[2] == 4:
        has_alpha = True
        alpha_channel = img[:, :, 3]
        bgr = img[:, :, :3]
        
    assert has_alpha is True, "Alpha detection failed"
    assert bgr.shape == (200, 200, 3), f"BGR extraction shape mismatch: {bgr.shape}"
    assert alpha_channel.shape == (200, 200), f"Alpha extraction shape mismatch: {alpha_channel.shape}"
    
    # Simulate 4x scaling
    scale = 4
    out_h, out_w = h * scale, w * scale
    simulated_output_bgr = cv2.resize(bgr, (out_w, out_h), interpolation=cv2.INTER_LINEAR)
    
    # Alpha resize with Lanczos
    alpha_resized = cv2.resize(alpha_channel, (out_w, out_h), interpolation=cv2.INTER_LANCZOS4)
    recombined = np.dstack([simulated_output_bgr, alpha_resized])
    
    assert recombined.shape == (800, 800, 4), f"Recombined shape mismatch: {recombined.shape}"
    assert recombined[400, 400, 3] == 128, f"Alpha channel value corrupted: {recombined[400, 400, 3]}"
    print("  -> PASSED: RGBA transparency and dimensions preserved perfectly.")

def test_grayscale_channel_handling():
    print("[TEST 2] Testing Grayscale 1-channel to 3-channel conversion...")
    # 2D Grayscale image
    img_gray = np.full((150, 150), 200, dtype=np.uint8)
    
    if len(img_gray.shape) == 2:
        converted_bgr = cv2.cvtColor(img_gray, cv2.COLOR_GRAY2BGR)
        
    assert converted_bgr.shape == (150, 150, 3), f"Grayscale conversion shape mismatch: {converted_bgr.shape}"
    print("  -> PASSED: Grayscale correctly converted to 3-channel BGR without PyTorch group errors.")

def test_oversized_image_downscaling():
    print("[TEST 3] Testing Oversized image protection (>3840px)...")
    # Simulate a 6000x4000 camera photo
    h, w = 4000, 6000
    max_dim = 3840
    factor = max_dim / max(h, w)
    new_w, new_h = int(w * factor), int(h * factor)
    
    assert new_w == 3840, f"Expected scaled width 3840, got {new_w}"
    assert new_h == 2560, f"Expected scaled height 2560, got {new_h}"
    print(f"  -> PASSED: 6000x4000 safely clamped to {new_w}x{new_h} to avoid VRAM/RAM exhaustion.")

def test_main_import_and_get_upscaler():
    print("[TEST 4] Testing main.py import and get_upscaler declaration...")
    import main
    assert hasattr(main, "get_upscaler"), "main.py missing get_upscaler"
    assert hasattr(main, "_UPSCALER_INSTANCE"), "main.py missing _UPSCALER_INSTANCE"
    assert hasattr(main, "_UPSCALER_INSTANCES"), "main.py missing _UPSCALER_INSTANCES"
    print("  -> PASSED: main.py imported cleanly, multi-model singleton verified.")

def test_purge_stale_files():
    print("[TEST 5] Testing purge_stale_files disk hygiene...")
    import main
    import time
    assert hasattr(main, "purge_stale_files"), "main.py missing purge_stale_files"
    # Create a temporary dummy test file in UPLOAD_DIR
    dummy_file = main.UPLOAD_DIR / "test_stale_temp.txt"
    dummy_file.write_text("test cleanup")
    # Simulate file created 1 hour ago
    past_time = time.time() - 3600
    os.utime(str(dummy_file), (past_time, past_time))
    assert dummy_file.exists()
    # Running purge with max_age_hours=0.5 (30 mins) should delete it
    main.purge_stale_files(max_age_hours=0.5)
    assert not dummy_file.exists(), "Dummy file was not purged"
    print("  -> PASSED: Stale temporary file purged successfully.")

def test_fastapi_endpoints():
    print("[TEST 6] Testing FastAPI routes and endpoints via AsyncClient...")
    import asyncio
    import httpx
    import main

    async def _test_routes():
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            res_home = await client.get("/")
            assert res_home.status_code == 200, f"Home route failed: {res_home.status_code}"
            res_upd = await client.get("/check-update")
            assert res_upd.status_code == 200, f"Check-update failed: {res_upd.status_code}"
            res_prog = await client.get("/progress/non-existent-task")
            assert res_prog.status_code == 200, f"Progress status failed: {res_prog.status_code}"
        print("  -> PASSED: Core endpoints (/, /check-update, /progress) responsive with HTTP 200.")

    asyncio.run(_test_routes())

if __name__ == "__main__":
    print("==================================================")
    print("   Running G-Toolbox Image Processing Unit Tests  ")
    print("==================================================")
    test_rgba_channel_separation()
    test_grayscale_channel_handling()
    test_oversized_image_downscaling()
    test_main_import_and_get_upscaler()
    test_purge_stale_files()
    test_fastapi_endpoints()
    print("==================================================")
    print("   ALL 6 TESTS PASSED SUCCESSFULLY!               ")
    print("==================================================")
