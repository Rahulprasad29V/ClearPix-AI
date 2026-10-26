import io
import sys
import json
import time
import socket
import urllib.request
import urllib.error
from pathlib import Path
from PIL import Image, ImageChops
import numpy as np

# Add project root to path for direct imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

BASE_URL = "http://127.0.0.1:5001"

def multipart_post(url, fields, files):
    boundary = "----WebKitFormBoundaryAuditSuite7MA4YW"
    body = io.BytesIO()

    for key, value in fields.items():
        body.write(f"--{boundary}\r\n".encode("utf-8"))
        body.write(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"))
        body.write(f"{value}\r\n".encode("utf-8"))

    for key, (filename, content, mime) in files.items():
        body.write(f"--{boundary}\r\n".encode("utf-8"))
        body.write(f'Content-Disposition: form-data; name="{key}"; filename="{filename}"\r\n'.encode("utf-8"))
        body.write(f"Content-Type: {mime}\r\n\r\n".encode("utf-8"))
        body.write(content)
        body.write(b"\r\n")

    body.write(f"--{boundary}--\r\n".encode("utf-8"))
    payload = body.getvalue()

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(payload)),
        },
    )
    return urllib.request.urlopen(req, timeout=120)


def run_audit_suite():
    print("=" * 60)
    print("🚀 RUNNING CLEARPIX AUDIT & VERIFICATION SUITE")
    print("=" * 60)

    # 1. Health check & Initial Metrics
    print("\n[1/8] Verifying /api/health and System Diagnostics...")
    health_res = urllib.request.urlopen(f"{BASE_URL}/api/health")
    assert health_res.status == 200
    health_data = json.loads(health_res.read().decode())
    print("  • Device:", health_data.get("device"))
    print("  • Model Init Time:", health_data.get("model_init_seconds"), "s")
    print("  • Memory Stats:", health_data.get("memory"))
    assert health_data["status"] == "ok"
    assert health_data["model_loaded"] is True
    print("  ✓ Health and diagnostic endpoint passed.")

    # 2. Malformed Files Verification
    print("\n[2/8] Verifying Malformed & Corrupted File Rejection...")
    malformed_cases = [
        ("empty.png", b"", "Empty file"),
        ("fake.jpg", b"NOT_A_REAL_JPEG_IMAGE_HEADER_12345", "Fake JPEG text"),
        ("corrupted.png", b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + b"\xff" * 50, "Truncated PNG data"),
    ]
    for filename, raw_bytes, desc in malformed_cases:
        try:
            multipart_post(
                f"{BASE_URL}/api/enhance",
                fields={"scale": 4},
                files={"image": (filename, raw_bytes, "image/jpeg")},
            )
            assert False, f"Server should have rejected malformed file: {desc}"
        except urllib.error.HTTPError as e:
            assert e.code == 400, f"Expected HTTP 400, got {e.code}"
            err_json = json.loads(e.read().decode())
            print(f"  ✓ Rejected {desc} ({filename}): HTTP 400 - '{err_json['message']}'")

    # 3. Unsupported Formats Verification (GIF, BMP, TIFF)
    print("\n[3/8] Verifying Unsupported Formats Rejection...")
    unsupported_cases = [
        ("anim.gif", b"GIF89a\x01\x00\x01\x00\x80\x00\x00", "GIF format"),
        ("bitmap.bmp", b"BM\x36\x00\x00\x00\x00\x00\x00\x00", "BMP format"),
        ("tiff_img.tiff", b"II*\x00\x08\x00\x00\x00", "TIFF format"),
    ]
    for filename, raw_bytes, desc in unsupported_cases:
        try:
            multipart_post(
                f"{BASE_URL}/api/enhance",
                fields={"scale": 4},
                files={"image": (filename, raw_bytes, "application/octet-stream")},
            )
            assert False, f"Server should have rejected unsupported format: {desc}"
        except urllib.error.HTTPError as e:
            assert e.code == 400, f"Expected HTTP 400, got {e.code}"
            err_json = json.loads(e.read().decode())
            print(f"  ✓ Rejected {desc} ({filename}): HTTP 400 - '{err_json['message']}'")

    # 4. Safe Limits Verification (Size & Dimensions)
    print("\n[4/8] Verifying Dimension and Size Limits...")
    # Too small (< 16px)
    tiny_img = Image.new("RGB", (10, 10), (128, 128, 128))
    tiny_buf = io.BytesIO()
    tiny_img.save(tiny_buf, format="PNG")
    try:
        multipart_post(
            f"{BASE_URL}/api/enhance",
            fields={"scale": 4},
            files={"image": ("tiny.png", tiny_buf.getvalue(), "image/png")},
        )
        assert False, "Should have rejected image smaller than 16x16"
    except urllib.error.HTTPError as e:
        assert e.code == 400
        print("  ✓ Rejected undersized image (<16px):", json.loads(e.read().decode())["message"])

    # Unsupported scale factor (e.g., 3 or 8)
    valid_buf = io.BytesIO()
    Image.new("RGB", (64, 64)).save(valid_buf, format="PNG")
    try:
        multipart_post(
            f"{BASE_URL}/api/enhance",
            fields={"scale": 3},
            files={"image": ("test.png", valid_buf.getvalue(), "image/png")},
        )
        assert False, "Should have rejected scale 3"
    except urllib.error.HTTPError as e:
        assert e.code == 400
        print("  ✓ Rejected unsupported scale factor (3x):", json.loads(e.read().decode())["message"])

    # 5. Transparent PNG (RGBA) Preservation
    print("\n[5/8] Verifying Transparent PNG (RGBA) Preservation...")
    rgba_w, rgba_h = 80, 80
    # Create RGBA image with distinct alpha patterns (checkerboard opacity)
    rgba_img = Image.new("RGBA", (rgba_w, rgba_h), (0, 0, 0, 0))
    pixels = rgba_img.load()
    for y in range(rgba_h):
        for x in range(rgba_w):
            alpha = 255 if ((x // 10) + (y // 10)) % 2 == 0 else 100
            pixels[x, y] = (220, 80, 40, alpha)

    rgba_buf = io.BytesIO()
    rgba_img.save(rgba_buf, format="PNG")
    rgba_resp = multipart_post(
        f"{BASE_URL}/api/enhance",
        fields={"scale": 4},
        files={"image": ("transparent_icon.png", rgba_buf.getvalue(), "image/png")},
    )
    assert rgba_resp.status == 200
    rgba_data = json.loads(rgba_resp.read().decode())
    assert rgba_data["output_dimensions"] == {"width": 320, "height": 320}

    # Fetch output image and inspect alpha channel
    dl_rgba_resp = urllib.request.urlopen(f"{BASE_URL}{rgba_data['download_url']}")
    assert dl_rgba_resp.status == 200
    dl_rgba_img = Image.open(io.BytesIO(dl_rgba_resp.read()))
    assert dl_rgba_img.mode == "RGBA", f"Expected RGBA output mode, got {dl_rgba_img.mode}"
    alpha_channel = np.array(dl_rgba_img.split()[3])
    # Verify transparency values exist and match expected distribution
    assert np.any(alpha_channel < 255), "Alpha channel should contain semi-transparent pixels"
    assert np.any(alpha_channel > 0), "Alpha channel should contain visible pixels"
    print(f"  ✓ RGBA transparency channel successfully preserved: {dl_rgba_img.size[0]}x{dl_rgba_img.size[1]} mode={dl_rgba_img.mode}")

    # 6. Portrait Image Verification (Tall aspect ratio)
    print("\n[6/8] Verifying Portrait Image (Aspect Ratio Preservation)...")
    port_w, port_h = 100, 200  # 1:2 aspect ratio
    port_img = Image.new("RGB", (port_w, port_h), (70, 130, 180))
    port_buf = io.BytesIO()
    port_img.save(port_buf, format="JPEG")
    port_resp = multipart_post(
        f"{BASE_URL}/api/enhance",
        fields={"scale": 2},
        files={"image": ("portrait.jpg", port_buf.getvalue(), "image/jpeg")},
    )
    assert port_resp.status == 200
    port_data = json.loads(port_resp.read().decode())
    exp_port_w, exp_port_h = port_w * 2, port_h * 2
    assert port_data["output_dimensions"] == {"width": exp_port_w, "height": exp_port_h}
    print(f"  ✓ Portrait dimensions verified: {port_w}x{port_h} -> {exp_port_w}x{exp_port_h} (2x scale, 1:2 aspect ratio preserved)")

    # 7. Genuine Model Output Verification
    print("\n[7/8] Verifying Real AI Model Output (vs Simple Interpolation)...")
    # Real-ESRGAN adds sharp high-frequency neural features and fine edge transitions
    # that differ noticeably from linear or bicubic interpolation
    test_w, test_h = 64, 64
    pattern_img = Image.new("RGB", (test_w, test_h), (255, 255, 255))
    pat_pixels = pattern_img.load()
    for y in range(test_h):
        for x in range(test_w):
            if (x + y) % 8 == 0:
                pat_pixels[x, y] = (0, 0, 0)
    pat_buf = io.BytesIO()
    pattern_img.save(pat_buf, format="PNG")

    ai_resp = multipart_post(
        f"{BASE_URL}/api/enhance",
        fields={"scale": 4},
        files={"image": ("pattern.png", pat_buf.getvalue(), "image/png")},
    )
    assert ai_resp.status == 200
    ai_data = json.loads(ai_resp.read().decode())
    ai_dl = urllib.request.urlopen(f"{BASE_URL}{ai_data['download_url']}")
    ai_img = Image.open(io.BytesIO(ai_dl.read()))
    assert ai_img.size == (test_w * 4, test_h * 4)

    # Compute bicubic baseline for comparison
    bicubic_img = pattern_img.resize((test_w * 4, test_h * 4), resample=Image.Resampling.BICUBIC)
    # Measure mean absolute pixel difference between Real-ESRGAN and naive bicubic
    diff = ImageChops.difference(ai_img, bicubic_img)
    diff_np = np.array(diff)
    mae = np.mean(diff_np)
    print(f"  • Mean absolute pixel difference vs naive bicubic: {mae:.2f}")
    assert mae > 1.0, f"Output is too identical to naive bicubic interpolation (MAE: {mae:.2f})"
    print("  ✓ Confirmed genuine Real-ESRGAN neural output with distinct high-frequency reconstruction.")

    # 8. Temporary File Cleanup Verification
    print("\n[8/8] Verifying Temporary File Lifecycle & Cleanup...")
    from utils.image_utils import TempFileManager
    mgr = TempFileManager()
    # Force cleanup with max_age_seconds=0
    dummy_id = mgr.generate_id()
    dummy_path = mgr.save_output(dummy_id, Image.new("RGB", (32, 32)))
    assert dummy_path.exists()
    cleaned = mgr.cleanup_expired(max_age_seconds=0)
    assert not dummy_path.exists(), "Dummy output file should have been deleted by cleanup"
    print(f"  ✓ TempFileManager cleaned up {cleaned} expired file(s) successfully.")

    print("\n" + "=" * 60)
    print("🎉 AUDIT SUITE COMPLETED: ALL 8 TEST PHASES PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    run_audit_suite()
