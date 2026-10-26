# ClearPix — Production AI Photo Super-Resolution Engine

ClearPix is a production-ready AI photo upscaler inspired by the minimalist aesthetics of Crisp Photos. It is powered by the official **Real-ESRGAN x4plus** deep neural network, delivering genuine blind super-resolution with realistic texture synthesis and crisp edge reconstruction locally on Apple Silicon (`mps`).

---

## 1. Key Features

- **Official Real-ESRGAN x4plus Neural Network**:
  - Full 23-block **RRDBNet** (Residual-in-Residual Dense Network) with 64 feature channels, 32 growth channels, and $4\times$ native upsampling.
  - Automatically downloads and verifies model checkpoint (`RealESRGAN_x4plus.pth`, $67\text{ MB}$) on boot.
- **Apple Silicon GPU Acceleration (MPS)**:
  - Accelerates convolutional kernels directly on the Apple Silicon GPU cores via PyTorch Metal Performance Shaders (`mps`).
  - Automatic fallback to CPU if MPS is unavailable.
- **Tiled Streaming Inference Engine**:
  - Automatically slices large images into $512\text{ px}$ tiles with $10\text{ px}$ padding.
  - Streams completed tiles directly to CPU memory (`.cpu()`), preventing unified VRAM thrashing and keeping peak GPU memory under $70\text{ MB}$.
- **$2\times$ and $4\times$ Scale Controls**:
  - **$4\times$**: Direct native inference from the Real-ESRGAN model.
  - **$2\times$**: High-fidelity super-resolution followed by anti-aliased Lanczos downsampling.
- **Synchronized Comparison Viewer with Zoom & Pan**:
  - Draggable split-view slider with synchronized before/after image display.
  - Floating zoom toolbar with **Zoom In (+)**, **Zoom Out (−)**, **1:1 Actual Pixels**, **Fit to Screen**, and **2× Detail Zoom**.
  - Smooth pan dragging when zoomed in, with mouse wheel zoom support.
- **Output Metadata Grid**:
  - Real-time display of original dimensions, enhanced dimensions, scale factor, pure inference duration, and active hardware accelerator.
- **Honest Status Indicator**:
  - Stage-by-stage progress feedback (Validation $\rightarrow$ Model Dispatch $\rightarrow$ Super-Resolution $\rightarrow$ Tile Assembly $\rightarrow$ PNG Encoding) with an active elapsed timer and user Cancel option.
- **Security & Concurrency Safeguards**:
  - File size ($25\text{ MB}$), dimension ($16\text{ px}$ to $4096\text{ px}$), and resolution ($16\text{ Megapixels}$) limits.
  - Pillow decompression bomb protection (`Image.MAX_IMAGE_PIXELS = 32,000,000`).
  - Threading concurrency semaphore (`INFERENCE_SEMAPHORE = 1`) with $5\text{s}$ timeout preventing unified memory crashes.
  - Automated temporary file expiration cleanup.

---

## 2. Quickstart & Local Setup

### Prerequisites
- macOS 12 Monterey or newer (optimized for Apple Silicon M1/M2/M3/M4).
- Python 3.10 – 3.14.

### 1. Clone & Set Up Virtual Environment

```bash
cd crisp_clone

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate
```

### 2. Install Pinned Dependencies

```bash
pip install -r requirements.txt
```

### 3. Download Model Weights (Optional Manual Setup)

Weights are downloaded automatically on first startup, or manually via:

```bash
python scripts/download_model.py
```

### 4. Run Development Server

```bash
python app.py
```

Open [http://127.0.0.1:5001](http://127.0.0.1:5001) in your browser.

---

## 3. Production Deployment with Gunicorn

For production deployments, ClearPix includes a dedicated [`gunicorn.conf.py`](gunicorn.conf.py) configuration:

```bash
# Launch with Gunicorn WSGI server
.venv/bin/gunicorn -c gunicorn.conf.py app:app
```

### Production Configuration Summary:
- **Workers**: `1` (Single worker is required for local GPU/MPS inference to avoid duplicating model weights across multiple processes).
- **Threads**: `4` (Handles non-blocking concurrent requests for previews, downloads, and health checks while inference runs).
- **Timeout**: `300s` (Allows complete execution for large panoramic images).
- **Port**: Configurable via `PORT` environment variable (default: `5001`).

---

## 4. Benchmark Performance Metrics

Repeatable benchmark results on an Apple Silicon M1 (arm64, 8 cores, MPS active) using [`tests/benchmark.py`](tests/benchmark.py):

| Metric | $2\times$ Scale ($\text{Mean} \pm \sigma$) | $4\times$ Scale ($\text{Mean} \pm \sigma$) |
| :--- | :--- | :--- |
| **Model Cold-Start Init** | **0.324 s** | **0.324 s** |
| **Pure AI Inference Time** | **$2.477 \pm 0.372\text{ s}$** | **$2.088 \pm 0.081\text{ s}$** |
| **Total Request Round-Trip** | **$2.648 \pm 0.386\text{ s}$** | **$2.582 \pm 0.077\text{ s}$** |
| **Peak Process RSS Memory** | **$452.2\text{ MB}$** | **$452.2\text{ MB}$** |
| **MPS VRAM Allocated** | **$64.6\text{ MB}$** | **$64.6\text{ MB}$** |
| **Input Dimensions** | $320 \times 240\text{ px}$ | $320 \times 240\text{ px}$ |
| **Output Dimensions** | $640 \times 480\text{ px}$ | $1280 \times 960\text{ px}$ |

*Tested on macOS Apple Silicon. 100% genuine Real-ESRGAN neural output.*

---

## 5. API Reference

### `GET /api/health`
Health check and diagnostic endpoint reporting model readiness and memory utilization:
```json
{
  "status": "ok",
  "app": "ClearPix AI Photo Upscaler",
  "model_name": "RealESRGAN_x4plus",
  "model_loaded": true,
  "model_init_seconds": 0.324,
  "device": "mps",
  "architecture": "RRDBNet (num_feat=64, num_block=23, scale=4)",
  "memory": {
    "device": "mps",
    "mps_allocated_mb": 63.73,
    "mps_driver_mb": 64.38,
    "peak_rss_mb": 452.23
  }
}
```

### `POST /api/enhance`
Accepts multipart form-data and executes Real-ESRGAN super-resolution:
- **Parameters**:
  - `image` (file): JPEG, PNG, or WebP (up to 25 MB).
  - `scale` (int): `2` or `4` (default `4`).
- **Response**:
  ```json
  {
    "status": "success",
    "id": "e3b0c44298fc1c149afbf4c8996fb924",
    "original_filename": "photo.jpg",
    "original_dimensions": {"width": 2054, "height": 766},
    "output_dimensions": {"width": 8216, "height": 3064},
    "scale": 4,
    "device": "mps",
    "duration_seconds": 43.81,
    "timing": {
      "model_init_seconds": 0.324,
      "inference_seconds": 43.81,
      "total_request_seconds": 44.44
    },
    "preview_url": "/api/preview/e3b0c44298fc1c149afbf4c8996fb924",
    "download_url": "/api/download/e3b0c44298fc1c149afbf4c8996fb924"
  }
  ```

### `GET /api/preview/<id>`
Serves the super-resolved PNG image for inline rendering.

### `GET /api/download/<id>`
Triggers an attachment download with a clean sanitized filename (e.g. `photo-enhanced-4x.png`).

---

## 6. Automated Testing

ClearPix includes three automated test suites:

```bash
# 1. Run standard unit test suite (health, limits, formats, scaling, downloads)
.venv/bin/python -m unittest tests/test_suite.py

# 2. Run complete 8-phase audit suite (malformed data, transparency, model verification)
.venv/bin/python tests/test_audit_suite.py

# 3. Run repeatable 2x and 4x benchmark
.venv/bin/python tests/benchmark.py
```
