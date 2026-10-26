import io
import os
import sys
import json
import time
import math
import argparse
import urllib.request
from pathlib import Path
from PIL import Image, ImageDraw

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

BASE_URL = os.environ.get("CLEARPIX_URL", "http://127.0.0.1:5001")


def generate_benchmark_image(path: Path, width: int = 320, height: int = 240) -> bytes:
    """Generate a reproducible, detail-rich benchmark photo with geometric textures and gradients."""
    img = Image.new("RGB", (width, height), (240, 240, 235))
    draw = ImageDraw.Draw(img)

    # Background gradient
    for y in range(height):
        r = int(30 + 150 * (y / height))
        g = int(60 + 120 * (1 - y / height))
        b = int(120 + 80 * (y / height))
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # High-frequency geometric patterns (simulating hair/foliage textures)
    for i in range(0, width, 16):
        draw.line([(i, 0), (i + 40, height)], fill=(255, 255, 255), width=2)
        draw.line([(width - i, 0), (width - i - 40, height)], fill=(40, 20, 10), width=1)

    # Fine concentric circles
    cx, cy = width // 2, height // 2
    for rad in range(10, 80, 8):
        draw.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], outline=(220, 230, 80), width=2)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    data = buf.getvalue()
    if path:
        path.write_bytes(data)
    return data


def multipart_post(url, fields, files):
    boundary = "----WebKitFormBoundaryBench7MA4YW"
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


def calc_stats(values):
    if not values:
        return 0.0, 0.0, 0.0, 0.0
    n = len(values)
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / (n - 1) if n > 1 else 0.0
    stdev = math.sqrt(variance)
    return mean, stdev, min(values), max(values)


def run_benchmark(image_path: Path = None, runs: int = 3):
    print("=" * 78)
    print(" 📊 CLEARPIX REAL-ESRGAN x4PLUS AI BENCHMARK")
    print(f" Target Server: {BASE_URL}")
    print("=" * 78)

    # 1. Check health and get cold-start model init time
    try:
        health_res = urllib.request.urlopen(f"{BASE_URL}/api/health", timeout=10)
        health_data = json.loads(health_res.read().decode())
    except Exception as e:
        print(f"❌ Error connecting to server at {BASE_URL}: {e}")
        print("Please ensure the Flask app is running (.venv/bin/python app.py).")
        sys.exit(1)

    model_init_time = health_data.get("model_init_seconds", 0.0)
    device = health_data.get("device", "unknown")
    initial_mem = health_data.get("memory", {})

    print(f"\n[Environment Diagnostic]")
    print(f"  • AI Model:          {health_data.get('model_name')}")
    print(f"  • Architecture:      {health_data.get('architecture')}")
    print(f"  • Inference Device:  {device.upper()}")
    print(f"  • Model Init Time:   {model_init_time:.3f} s (cold-start initialization)")
    print(f"  • Baseline RSS Mem:  {initial_mem.get('peak_rss_mb', 0):.2f} MB")
    if device == "mps":
        print(f"  • Baseline MPS Mem:  {initial_mem.get('mps_allocated_mb', 0):.2f} MB (allocated)")

    # 2. Prepare test image
    if image_path and Path(image_path).exists():
        target_path = Path(image_path)
        img_bytes = target_path.read_bytes()
        print(f"\n[Benchmark Input Image]: {target_path.name} (Custom)")
    else:
        sample_path = PROJECT_ROOT / "tests" / "benchmark_test.jpg"
        img_bytes = generate_benchmark_image(sample_path, width=320, height=240)
        target_path = sample_path
        print(f"\n[Benchmark Input Image]: {sample_path.name} (Standard 320x240 detail test pattern)")

    pil_test = Image.open(io.BytesIO(img_bytes))
    in_w, in_h = pil_test.size
    print(f"  • Dimensions: {in_w} × {in_h} px")
    print(f"  • File Size:  {len(img_bytes) / 1024:.1f} KB")
    print(f"  • Repetitions: {runs} runs per scale factor (2x and 4x)\n")

    scales = [2, 4]
    all_results = {}

    for scale in scales:
        print("-" * 78)
        print(f" ⚙️  Benchmarking Scale: {scale}× ({in_w}×{in_h} -> {in_w * scale}×{in_h * scale}) | {runs} Runs")
        print("-" * 78)
        print(f"{'Run':<6}{'Inference (s)':<16}{'Total Req (s)':<16}{'Peak RSS (MB)':<16}{'MPS Alloc (MB)':<16}{'Output Shape':<14}")
        print("-" * 78)

        scale_runs = []

        for r in range(1, runs + 1):
            t_req_start = time.perf_counter()
            resp = multipart_post(
                f"{BASE_URL}/api/enhance",
                fields={"scale": scale},
                files={"image": (target_path.name, img_bytes, "image/jpeg")},
            )
            t_req_end = time.perf_counter()

            total_wall_time = t_req_end - t_req_start
            data = json.loads(resp.read().decode())

            timing = data.get("timing", {})
            inference_time = timing.get("inference_seconds", data.get("duration_seconds", 0.0))
            mem = data.get("memory", {})
            peak_rss = mem.get("peak_rss_mb", 0.0)
            mps_alloc = mem.get("mps_allocated_mb", 0.0)
            out_dim = f"{data['output_dimensions']['width']}x{data['output_dimensions']['height']}"

            scale_runs.append({
                "run": r,
                "inference_time": inference_time,
                "total_wall_time": total_wall_time,
                "peak_rss": peak_rss,
                "mps_alloc": mps_alloc,
                "out_dim": out_dim,
            })

            print(f"{r:<6}{inference_time:<16.3f}{total_wall_time:<16.3f}{peak_rss:<16.2f}{mps_alloc:<16.2f}{out_dim:<14}")
            # Brief pause between runs
            time.sleep(0.5)

        all_results[scale] = scale_runs

    # 3. Print Statistical Summary Table
    print("\n" + "=" * 78)
    print(" 📈 BENCHMARK STATISTICAL SUMMARY")
    print("=" * 78)
    print(f"{'Metric':<30}{'2× Scale (Mean ± σ)':<24}{'4× Scale (Mean ± σ)':<24}")
    print("-" * 78)

    inf_2x_mean, inf_2x_std, inf_2x_min, inf_2x_max = calc_stats([r["inference_time"] for r in all_results[2]])
    inf_4x_mean, inf_4x_std, inf_4x_min, inf_4x_max = calc_stats([r["inference_time"] for r in all_results[4]])
    print(f"{'AI Inference Time (s)':<30}{inf_2x_mean:.3f} ± {inf_2x_std:.3f} s{'':<7}{inf_4x_mean:.3f} ± {inf_4x_std:.3f} s")

    req_2x_mean, req_2x_std, req_2x_min, req_2x_max = calc_stats([r["total_wall_time"] for r in all_results[2]])
    req_4x_mean, req_4x_std, req_4x_min, req_4x_max = calc_stats([r["total_wall_time"] for r in all_results[4]])
    print(f"{'Total Request Time (s)':<30}{req_2x_mean:.3f} ± {req_2x_std:.3f} s{'':<7}{req_4x_mean:.3f} ± {req_4x_std:.3f} s")

    rss_2x_mean, rss_2x_std, _, _ = calc_stats([r["peak_rss"] for r in all_results[2]])
    rss_4x_mean, rss_4x_std, _, _ = calc_stats([r["peak_rss"] for r in all_results[4]])
    print(f"{'Peak Process RSS (MB)':<30}{rss_2x_mean:.1f} ± {rss_2x_std:.1f} MB{'':<6}{rss_4x_mean:.1f} ± {rss_4x_std:.1f} MB")

    if device == "mps":
        mps_2x_mean, _, _, _ = calc_stats([r["mps_alloc"] for r in all_results[2]])
        mps_4x_mean, _, _, _ = calc_stats([r["mps_alloc"] for r in all_results[4]])
        print(f"{'MPS VRAM Allocated (MB)':<30}{mps_2x_mean:.1f} MB{'':<17}{mps_4x_mean:.1f} MB")

    print("-" * 78)
    print(f"{'Model Cold-Start Init':<30}{model_init_time:.3f} s (One-time, persistent in memory)")
    print(f"{'Output Dimensions':<30}{in_w * 2} × {in_h * 2} px{'':<11}{in_w * 4} × {in_h * 4} px")
    print("=" * 78)

    # Save results to a json file for reproducible auditing
    benchmark_log = PROJECT_ROOT / "tests" / "benchmark_results.json"
    benchmark_log.write_text(json.dumps({
        "timestamp": time.time(),
        "device": device,
        "model_init_seconds": model_init_time,
        "input_dimensions": {"width": in_w, "height": in_h},
        "results": all_results,
        "summary": {
            "scale_2x": {
                "inference_mean": round(inf_2x_mean, 4),
                "inference_stdev": round(inf_2x_std, 4),
                "request_mean": round(req_2x_mean, 4),
                "request_stdev": round(req_2x_std, 4),
            },
            "scale_4x": {
                "inference_mean": round(inf_4x_mean, 4),
                "inference_stdev": round(inf_4x_std, 4),
                "request_mean": round(req_4x_mean, 4),
                "request_stdev": round(req_4x_std, 4),
            }
        }
    }, indent=2))
    print(f"✓ Results saved to {benchmark_log.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ClearPix AI Benchmark Suite")
    parser.add_argument("--image", type=str, default=None, help="Path to input image for benchmarking")
    parser.add_argument("--runs", type=int, default=3, help="Number of repetitions per scale (default: 3)")
    args = parser.parse_args()

    run_benchmark(image_path=args.image, runs=args.runs)
