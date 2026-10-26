import io
import json
import socket
import urllib.request
import urllib.parse
from PIL import Image

def find_server_port():
    for p in (5000, 5001, 5050, 8080):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', p)) == 0:
                try:
                    res = urllib.request.urlopen(f"http://127.0.0.1:{p}/api/health", timeout=1)
                    if res.status == 200:
                        return p
                except Exception:
                    pass
    return 5000

PORT = find_server_port()
BASE_URL = f"http://127.0.0.1:{PORT}"
print(f"Testing against active server on {BASE_URL}...")


def multipart_post(url, fields, files):
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
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
    return urllib.request.urlopen(req, timeout=300)


def test_health():
    print("\n--- 1. Testing /api/health ---")
    resp = urllib.request.urlopen(f"{BASE_URL}/api/health")
    assert resp.status == 200
    data = json.loads(resp.read().decode())
    print("Health response:", data)
    assert data["status"] == "ok"
    assert data["model_loaded"] is True
    assert data["device"] in ("mps", "cuda", "cpu")
    print("✓ Health endpoint passed.")


def test_enhance_shapes_and_scales():
    print("\n--- 2. Testing Landscape, Portrait, Square, RGBA & 2x/4x scales ---")

    test_cases = [
        ("landscape", 160, 100, "RGB", 4, 640, 400),
        ("portrait", 100, 160, "RGB", 4, 400, 640),
        ("square", 120, 120, "RGB", 4, 480, 480),
        ("rgba_transparent", 100, 100, "RGBA", 4, 400, 400),
        ("scale_2x", 140, 100, "RGB", 2, 280, 200),
    ]

    for name, w, h, mode, scale, exp_w, exp_h in test_cases:
        if mode == "RGBA":
            img = Image.new("RGBA", (w, h), (50, 100, 150, 180))
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            mime = "image/png"
            fname = f"{name}.png"
        else:
            img = Image.new("RGB", (w, h), (100, 150, 200))
            buf = io.BytesIO()
            img.save(buf, format="JPEG")
            mime = "image/jpeg"
            fname = f"{name}.jpg"

        file_bytes = buf.getvalue()

        resp = multipart_post(
            f"{BASE_URL}/api/enhance",
            fields={"scale": scale},
            files={"image": (fname, file_bytes, mime)},
        )
        assert resp.status == 200
        res_data = json.loads(resp.read().decode())
        out_w = res_data["output_dimensions"]["width"]
        out_h = res_data["output_dimensions"]["height"]
        print(f"  {name} ({w}x{h}, scale={scale}x) -> {out_w}x{out_h} in {res_data['duration_seconds']}s on {res_data['device']}")

        assert out_w == exp_w, f"Expected width {exp_w}, got {out_w}"
        assert out_h == exp_h, f"Expected height {exp_h}, got {out_h}"
        assert res_data["scale"] == scale

        # Test preview endpoint
        preview_resp = urllib.request.urlopen(f"{BASE_URL}{res_data['preview_url']}")
        assert preview_resp.status == 200
        assert preview_resp.headers.get("Content-Type") == "image/png"

        # Test download endpoint
        download_resp = urllib.request.urlopen(f"{BASE_URL}{res_data['download_url']}")
        assert download_resp.status == 200
        assert download_resp.headers.get("Content-Type") == "image/png"
        downloaded_bytes = download_resp.read()
        downloaded_img = Image.open(io.BytesIO(downloaded_bytes))
        assert downloaded_img.size == (exp_w, exp_h)
        if mode == "RGBA":
            assert downloaded_img.mode == "RGBA"

    print("✓ Landscape, Portrait, Square, RGBA & 2x/4x tests PASSED.")


def test_invalid_inputs():
    print("\n--- 3. Testing Error Handling & Validation ---")

    # 1. Invalid text file disguised as PNG
    try:
        multipart_post(
            f"{BASE_URL}/api/enhance",
            fields={"scale": 4},
            files={"image": ("test.png", b"Hello, this is not an image!", "image/png")},
        )
        assert False, "Should have rejected non-image"
    except urllib.error.HTTPError as e:
        assert e.code == 400
        err_data = json.loads(e.read().decode())
        print("  ✓ Correctly rejected fake image:", err_data["message"])

    # 2. Unsupported scale
    try:
        buf = io.BytesIO()
        Image.new("RGB", (64, 64)).save(buf, format="PNG")
        multipart_post(
            f"{BASE_URL}/api/enhance",
            fields={"scale": 8},
            files={"image": ("test.png", buf.getvalue(), "image/png")},
        )
        assert False, "Should have rejected scale 8"
    except urllib.error.HTTPError as e:
        assert e.code == 400
        err_data = json.loads(e.read().decode())
        print("  ✓ Correctly rejected invalid scale:", err_data["message"])

    # 3. Nonexistent result ID
    try:
        urllib.request.urlopen(f"{BASE_URL}/api/preview/00000000000000000000000000000000")
        assert False, "Should return 404 for missing preview"
    except urllib.error.HTTPError as e:
        assert e.code == 404
        print("  ✓ Correctly returned 404 for nonexistent preview")

    print("✓ All validation & error handling tests PASSED.")


if __name__ == "__main__":
    test_health()
    test_enhance_shapes_and_scales()
    test_invalid_inputs()
    print("\n==========================================")
    print("🎉 ALL END-TO-END TESTS PASSED SUCCESSFULLY!")
    print("==========================================")
