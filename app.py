import os
import time
import socket
import logging
import traceback
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, abort
from werkzeug.exceptions import RequestEntityTooLarge

from services.upscaler import RealESRGANService
from utils.image_utils import (
    validate_image_file,
    sanitize_filename,
    TempFileManager,
    MAX_FILE_SIZE,
)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s [%(name)s]: %(message)s",
)
logger = logging.getLogger("ClearPix.App")

app = Flask(__name__)
import threading

# Concurrency safeguard: Limit concurrent GPU inference to 1 job to prevent unified memory thrashing
INFERENCE_SEMAPHORE = threading.Semaphore(1)
CONCURRENCY_TIMEOUT_SECONDS = 60.0

# 30 MB maximum request payload limit
app.config["MAX_CONTENT_LENGTH"] = 30 * 1024 * 1024
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

@app.after_request
def add_header(response):
    if "static" in request.path or request.path == "/":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

temp_manager = TempFileManager()
# Initialize RealESRGAN singleton service (loads model once)
logger.info("Initializing RealESRGAN singleton service...")
upscaler_service = RealESRGANService()
logger.info(f"RealESRGAN service initialized on {upscaler_service.device_name}")

# In-memory dictionary for active job metadata (result_id -> info)
job_cache = {}


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/privacy")
def privacy():
    return render_template("privacy.html")


@app.get("/robots.txt")
def robots_txt():
    content = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /api/\n"
        "Disallow: /temp/\n"
        "\n"
        f"Sitemap: {request.host_url.rstrip('/')}/sitemap.xml\n"
    )
    return content, 200, {"Content-Type": "text/plain; charset=utf-8"}


@app.get("/sitemap.xml")
def sitemap_xml():
    base_url = request.host_url.rstrip("/")
    now_date = time.strftime("%Y-%m-%d")
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        "  <url>\n"
        f"    <loc>{base_url}/</loc>\n"
        f"    <lastmod>{now_date}</lastmod>\n"
        "    <changefreq>weekly</changefreq>\n"
        "    <priority>1.0</priority>\n"
        "  </url>\n"
        "  <url>\n"
        f"    <loc>{base_url}/privacy</loc>\n"
        f"    <lastmod>{now_date}</lastmod>\n"
        "    <changefreq>monthly</changefreq>\n"
        "    <priority>0.8</priority>\n"
        "  </url>\n"
        "</urlset>"
    )
    return xml, 200, {"Content-Type": "application/xml; charset=utf-8"}


@app.get("/api/health")
def health():
    status = upscaler_service.get_status()
    return jsonify(
        status="ok",
        app="ClearPix AI Photo Upscaler",
        model_name=status["model_name"],
        model_loaded=status["model_loaded"],
        model_init_seconds=status.get("model_init_seconds", 0.0),
        device=status["device"],
        architecture=status["architecture"],
        memory=status.get("memory", {}),
    )


@app.post("/api/enhance")
def enhance_image():
    req_start = time.time()
    # Periodically sweep expired temporary files
    temp_manager.cleanup_expired()

    if "image" not in request.files:
        logger.warning("Enhance request rejected: 'image' field missing from form-data")
        return jsonify(status="error", message="No image file provided in request."), 400

    file = request.files["image"]
    if not file or not file.filename:
        logger.warning("Enhance request rejected: empty or missing filename")
        return jsonify(status="error", message="Empty or missing file upload."), 400

    raw_filename = file.filename

    # Read scale parameter (default 4x, support 2x and 4x)
    try:
        scale = int(request.form.get("scale", 4))
    except (TypeError, ValueError):
        scale = 4

    if scale not in (2, 4):
        logger.warning(f"Enhance request rejected: invalid scale={scale}")
        return jsonify(status="error", message="Scale must be either 2 or 4."), 400

    logger.info(f"--> Received enhancement request: file='{raw_filename}', scale={scale}x")

    # Guard inference with concurrency semaphore
    acquired = INFERENCE_SEMAPHORE.acquire(timeout=CONCURRENCY_TIMEOUT_SECONDS)
    if not acquired:
        logger.warning(f"Enhance request rejected: server busy (concurrency limit reached for '{raw_filename}')")
        return (
            jsonify(
                status="error",
                message="Server is currently busy processing another image. Please wait a moment and try again.",
            ),
            503,
        )

    try:
        file_bytes = file.read()
        logger.info(f"Read {len(file_bytes)} bytes from upload stream")

        pil_image, detected_format = validate_image_file(file_bytes, raw_filename)
        orig_w, orig_h = pil_image.size
        logger.info(f"Validated {detected_format.upper()} image: dimensions={orig_w}x{orig_h}, mode={pil_image.mode}")

        # Run real AI inference through RealESRGANService
        logger.info(f"Dispatching image {orig_w}x{orig_h} to Real-ESRGAN inference pipeline (scale={scale}x)...")
        enhanced_image, out_w, out_h, duration = upscaler_service.enhance(
            pil_image, scale=scale
        )
        mem_stats = upscaler_service.get_memory_stats()

        result_id = temp_manager.generate_id()
        saved_path = temp_manager.save_output(result_id, enhanced_image)
        logger.info(f"Saved AI-enhanced output to {saved_path} (size={saved_path.stat().st_size} bytes)")

        download_name = sanitize_filename(raw_filename, scale=scale)
        job_cache[result_id] = {
            "download_name": download_name,
            "original_filename": Path(raw_filename).name,
            "orig_w": orig_w,
            "orig_h": orig_h,
            "out_w": out_w,
            "out_h": out_h,
            "scale": scale,
            "duration": round(duration, 2),
        }

        total_req_time = time.time() - req_start
        logger.info(
            f"<-- Completed request for '{raw_filename}': {orig_w}x{orig_h} -> {out_w}x{out_h} "
            f"in {total_req_time:.2f}s (inference: {duration:.2f}s on {upscaler_service.device_name}, "
            f"peak RSS: {mem_stats.get('peak_rss_mb', 0)} MB)"
        )

        return jsonify(
            status="success",
            id=result_id,
            original_filename=Path(raw_filename).name,
            original_dimensions={"width": orig_w, "height": orig_h},
            output_dimensions={"width": out_w, "height": out_h},
            scale=scale,
            device=upscaler_service.device_name,
            duration_seconds=round(duration, 2),
            timing={
                "model_init_seconds": round(getattr(upscaler_service, "model_init_time", 0.0), 3),
                "inference_seconds": round(duration, 3),
                "total_request_seconds": round(total_req_time, 3),
            },
            memory=mem_stats,
            preview_url=f"/api/preview/{result_id}",
            download_url=f"/api/download/{result_id}",
        )

    except ValueError as e:
        logger.warning(f"Validation failure for '{raw_filename}': {e}")
        return jsonify(status="error", message=str(e)), 400
    except TimeoutError as e:
        logger.error(f"Inference timeout for '{raw_filename}': {e}")
        return jsonify(status="error", message=str(e)), 504
    except RuntimeError as e:
        logger.error(f"Inference failure for '{raw_filename}':\n{traceback.format_exc()}")
        return (
            jsonify(
                status="error",
                message=f"AI enhancement failed during processing: {str(e)}",
            ),
            500,
        )
    except Exception as e:
        logger.error(f"Unexpected error processing '{raw_filename}':\n{traceback.format_exc()}")
        return (
            jsonify(
                status="error",
                message="An unexpected server error occurred during enhancement. Please check server logs.",
            ),
            500,
        )
    finally:
        INFERENCE_SEMAPHORE.release()


@app.get("/api/preview/<result_id>")
def preview_result(result_id: str):
    file_path = temp_manager.get_output_path(result_id)
    if not file_path:
        logger.warning(f"Preview request for nonexistent or expired result_id: {result_id}")
        abort(404, description="Result image not found or expired.")
    return send_file(
        str(file_path),
        mimetype="image/png",
        as_attachment=False,
        max_age=3600,
    )


@app.get("/api/download/<result_id>")
def download_result(result_id: str):
    file_path = temp_manager.get_output_path(result_id)
    if not file_path:
        logger.warning(f"Download request for nonexistent or expired result_id: {result_id}")
        abort(404, description="Result image not found or expired.")

    meta = job_cache.get(result_id, {})
    download_name = meta.get("download_name", f"enhanced-{result_id[:8]}.png")

    logger.info(f"Delivering download for result_id={result_id} as '{download_name}'")
    return send_file(
        str(file_path),
        mimetype="image/png",
        as_attachment=True,
        download_name=download_name,
        max_age=0,
    )


@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(e):
    logger.warning("Upload rejected: payload exceeds MAX_CONTENT_LENGTH")
    return (
        jsonify(
            status="error",
            message=f"File exceeds maximum allowed size ({MAX_FILE_SIZE // (1024*1024)} MB).",
        ),
        413,
    )


@app.errorhandler(404)
def handle_not_found(e):
    if request.path.startswith("/api/"):
        return jsonify(status="error", message="Resource not found."), 404
    return render_template("index.html"), 404


@app.errorhandler(500)
def handle_server_error(e):
    logger.error("Internal Server Error (500) triggered")
    return jsonify(status="error", message="Internal server error."), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    debug = os.environ.get("FLASK_DEBUG") == "1"

    def is_port_in_use(p):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("127.0.0.1", p)) == 0

    if "PORT" not in os.environ and is_port_in_use(port):
        for candidate in (5001, 5050, 8080, 5000):
            if not is_port_in_use(candidate):
                port = candidate
                break

    print(f" * Serving ClearPix AI Upscaler on http://127.0.0.1:{port}")
    print(f" * Active hardware accelerator: {upscaler_service.device_name}")
    app.run(host="127.0.0.1", port=port, debug=debug)
