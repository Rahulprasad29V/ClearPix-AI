import os

# ClearPix Real-ESRGAN Production Gunicorn Configuration

port = os.environ.get("PORT", "5001")
bind = f"0.0.0.0:{port}"

# Single worker is recommended for local GPU/MPS inference to avoid duplicating
# the 67 MB model weights and competing for unified Apple Silicon memory.
workers = int(os.environ.get("WEB_CONCURRENCY", 1))

# Threads handle non-blocking concurrent requests (health, previews, downloads)
threads = int(os.environ.get("GUNICORN_THREADS", 4))

# Allow sufficient timeout for deep neural super-resolution on high-resolution images
timeout = int(os.environ.get("GUNICORN_TIMEOUT", 300))
graceful_timeout = 30
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("LOG_LEVEL", "info")

# Process naming
proc_name = "clearpix-upscaler"
