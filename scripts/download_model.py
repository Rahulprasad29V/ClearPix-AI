#!/usr/bin/env python3
"""
Model download script for Real-ESRGAN x4plus.
Downloads pretrained weights to models/RealESRGAN_x4plus.pth.
"""

import sys
import urllib.request
from pathlib import Path

MODEL_URL = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"
EXPECTED_SIZE = 67040989  # approx 67 MB


def download_weights(target_dir: Path):
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / "RealESRGAN_x4plus.pth"

    if target_path.exists():
        actual_size = target_path.stat().st_size
        if actual_size >= 60 * 1024 * 1024:
            print(f"✓ Model weights already exist at {target_path} ({actual_size / (1024*1024):.1f} MB)")
            return True

    print(f"Downloading RealESRGAN_x4plus weights from:\n  {MODEL_URL}\nTo:\n  {target_path}...")
    temp_path = target_path.with_suffix(".tmp")
    try:
        req = urllib.request.Request(
            MODEL_URL,
            headers={"User-Agent": "Mozilla/5.0 ClearPix-Downloader/1.0"},
        )
        with urllib.request.urlopen(req) as resp, open(temp_path, "wb") as f:
            total_size = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            chunk_size = 1024 * 1024  # 1 MB
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total_size:
                    pct = (downloaded / total_size) * 100
                    print(f"\r  Progress: {pct:.1f}% ({downloaded / (1024*1024):.1f} / {total_size / (1024*1024):.1f} MB)", end="", flush=True)

        print("\nVerifying file size...")
        actual_size = temp_path.stat().st_size
        if actual_size < 60 * 1024 * 1024:
            raise RuntimeError(f"Downloaded file too small: {actual_size} bytes")

        temp_path.replace(target_path)
        print(f"✓ Successfully installed weights to {target_path} ({actual_size / (1024*1024):.1f} MB)")
        return True
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        print(f"\n✗ Download failed: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    models_dir = project_root / "models"
    success = download_weights(models_dir)
    sys.exit(0 if success else 1)
