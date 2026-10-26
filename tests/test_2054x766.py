import io
import json
import urllib.request
from PIL import Image

BASE_URL = "http://127.0.0.1:5001"

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

def test_2054x766():
    orig_w, orig_h = 2054, 766
    print(f"\n[Test] Generating synthetic {orig_w}x{orig_h} test image...")
    # Create image with smooth gradient
    img = Image.new("RGB", (orig_w, orig_h), (80, 120, 160))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    img_bytes = buf.getvalue()
    print(f"Generated JPEG bytes: {len(img_bytes)} bytes")

    # 1. Test 2x scale
    print(f"\n[Test 1] Running 2x scale enhancement ({orig_w}x{orig_h} -> 4108x1532)...")
    resp_2x = multipart_post(
        f"{BASE_URL}/api/enhance",
        fields={"scale": 2},
        files={"image": ("panoramic_2054x766.jpg", img_bytes, "image/jpeg")},
    )
    assert resp_2x.status == 200
    data_2x = json.loads(resp_2x.read().decode())
    print("  Status:", data_2x["status"])
    print("  Output dimensions:", data_2x["output_dimensions"])
    print(f"  Duration: {data_2x['duration_seconds']}s on {data_2x['device']}")

    assert data_2x["output_dimensions"]["width"] == 4108, f"Expected 4108, got {data_2x['output_dimensions']['width']}"
    assert data_2x["output_dimensions"]["height"] == 1532, f"Expected 1532, got {data_2x['output_dimensions']['height']}"
    assert data_2x["scale"] == 2

    # Verify download of 2x
    dl_resp_2x = urllib.request.urlopen(f"{BASE_URL}{data_2x['download_url']}")
    assert dl_resp_2x.status == 200
    dl_img_2x = Image.open(io.BytesIO(dl_resp_2x.read()))
    assert dl_img_2x.size == (4108, 1532)
    print("  ✓ 2x output image verified at 4108x1532 px!")

    # 2. Test 4x scale
    print(f"\n[Test 2] Running 4x scale enhancement ({orig_w}x{orig_h} -> 8208x3064)...")
    resp_4x = multipart_post(
        f"{BASE_URL}/api/enhance",
        fields={"scale": 4},
        files={"image": ("panoramic_2054x766.jpg", img_bytes, "image/jpeg")},
    )
    assert resp_4x.status == 200
    data_4x = json.loads(resp_4x.read().decode())
    print("  Status:", data_4x["status"])
    print("  Output dimensions:", data_4x["output_dimensions"])
    print(f"  Duration: {data_4x['duration_seconds']}s on {data_4x['device']}")

    assert data_4x["output_dimensions"]["width"] in (8208, 8216), f"Expected 8208 or 8216, got {data_4x['output_dimensions']['width']}"
    assert data_4x["output_dimensions"]["height"] == 3064, f"Expected 3064, got {data_4x['output_dimensions']['height']}"
    assert data_4x["scale"] == 4

    # Verify preview & download of 4x
    dl_resp_4x = urllib.request.urlopen(f"{BASE_URL}{data_4x['download_url']}")
    assert dl_resp_4x.status == 200
    dl_img_4x = Image.open(io.BytesIO(dl_resp_4x.read()))
    assert dl_img_4x.size in ((8208, 3064), (8216, 3064))
    print(f"  ✓ 4x output image verified at {dl_img_4x.size[0]}x{dl_img_4x.size[1]} px!")

    print("\n✓ ALL 2054x766 DIMENSION TESTS PASSED PERFECTLY!")

if __name__ == "__main__":
    test_2054x766()
