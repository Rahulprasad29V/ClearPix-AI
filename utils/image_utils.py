import io
import re
import time
import uuid
import logging
from pathlib import Path
from typing import Tuple, Optional
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

# Configurable limits
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB
MIN_DIMENSION = 16
MAX_DIMENSION = 4096
MAX_TOTAL_PIXELS = 16_000_000  # 16 Megapixels
FILE_RETENTION_SECONDS = 3600  # 1 hour lifetime for temporary files

# Pillow DecompressionBomb protection limit
Image.MAX_IMAGE_PIXELS = 32_000_000


def validate_image_file(file_bytes: bytes, original_filename: str = "") -> Tuple[Image.Image, str]:
    """
    Validate file magic bytes, MIME signature, size, dimensions, and image integrity.
    
    Returns:
        (PIL.Image, detected_format_extension)
    Raises:
        ValueError if file is invalid, corrupt, or exceeds limits.
    """
    if not file_bytes:
        raise ValueError("Uploaded file is empty.")

    if len(file_bytes) > MAX_FILE_SIZE:
        raise ValueError(f"File size exceeds maximum allowed limit ({MAX_FILE_SIZE // (1024*1024)} MB).")

    # Check file signature / magic bytes
    detected_format = None
    if file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        detected_format = "png"
    elif file_bytes.startswith(b"\xff\xd8\xff"):
        detected_format = "jpeg"
    elif file_bytes.startswith(b"RIFF") and len(file_bytes) >= 12 and file_bytes[8:12] == b"WEBP":
        detected_format = "webp"
    elif file_bytes.startswith((b"GIF87a", b"GIF89a")):
        raise ValueError("GIF images are not supported. Please upload a JPG, PNG, or WebP image.")
    elif file_bytes.startswith(b"BM"):
        raise ValueError("BMP images are not supported. Please upload a JPG, PNG, or WebP image.")
    elif file_bytes.startswith((b"II*\x00", b"MM\x00*")):
        raise ValueError("TIFF images are not supported. Please upload a JPG, PNG, or WebP image.")

    if not detected_format:
        raise ValueError("Unsupported or invalid image file signature. Only JPG, PNG, and WebP are accepted.")

    # Validate image decoding with Pillow
    try:
        buffer = io.BytesIO(file_bytes)
        img = Image.open(buffer)
        img.load()  # Force reading pixel data to detect truncated or corrupted files
        # Normalize EXIF orientation to ensure photos are never sideways
        transposed = ImageOps.exif_transpose(img)
        if transposed is not None:
            img = transposed
    except Exception as e:
        logger.warning(f"Image load verification failed: {e}")
        raise ValueError(f"Corrupted or malformed image data: {str(e)}")

    w, h = img.size
    if w < MIN_DIMENSION or h < MIN_DIMENSION:
        raise ValueError(f"Image dimensions ({w}x{h}) are too small. Minimum required is {MIN_DIMENSION}x{MIN_DIMENSION}px.")

    if w > MAX_DIMENSION or h > MAX_DIMENSION:
        raise ValueError(f"Image dimensions ({w}x{h}) exceed the maximum supported dimension ({MAX_DIMENSION}x{MAX_DIMENSION}px).")

    total_pixels = w * h
    if total_pixels > MAX_TOTAL_PIXELS:
        raise ValueError(
            f"Image resolution ({w}x{h} = {total_pixels:,} px) exceeds maximum limit of {MAX_TOTAL_PIXELS:,} pixels."
        )

    return img, detected_format


def sanitize_filename(filename: Optional[str], scale: int = 4) -> str:
    """Create a clean, safe download filename without path traversal risks."""
    if not filename:
        return f"clearpix-enhanced-{scale}x.png"

    # Strip paths
    name = Path(filename).name
    # Strip extension
    dot_idx = name.rfind(".")
    base = name[:dot_idx] if dot_idx > 0 else name
    # Sanitize characters
    clean_base = re.sub(r"[^\w\-.]", "_", base).strip("._")
    if not clean_base:
        clean_base = "image"
    return f"{clean_base}-enhanced-{scale}x.png"


class TempFileManager:
    """Manages temporary storage for uploads and enhanced outputs with automatic expiration."""

    def __init__(self, base_temp_dir: Optional[str] = None):
        project_root = Path(__file__).resolve().parent.parent
        self.base_dir = Path(base_temp_dir) if base_temp_dir else project_root / "temp"
        self.uploads_dir = self.base_dir / "uploads"
        self.outputs_dir = self.base_dir / "outputs"

        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)

    def generate_id(self) -> str:
        return uuid.uuid4().hex

    def save_output(self, result_id: str, pil_image: Image.Image) -> Path:
        """Save enhanced image as a lossless PNG in the outputs directory."""
        output_path = self.outputs_dir / f"{result_id}.png"
        # Optimize PNG save
        pil_image.save(output_path, format="PNG", optimize=True)
        return output_path

    def get_output_path(self, result_id: str) -> Optional[Path]:
        """Retrieve path to an output file if it exists and result_id is a valid hex UUID."""
        if not re.match(r"^[0-9a-f]{32}$", result_id):
            return None
        output_path = self.outputs_dir / f"{result_id}.png"
        if output_path.exists() and output_path.is_file():
            return output_path
        return None

    def cleanup_expired(self, max_age_seconds: int = FILE_RETENTION_SECONDS) -> int:
        """Delete temporary files older than the retention threshold. Returns count of deleted files."""
        now = time.time()
        deleted_count = 0
        for folder in (self.uploads_dir, self.outputs_dir):
            try:
                for file_path in folder.glob("*"):
                    if file_path.is_file():
                        try:
                            if now - file_path.stat().st_mtime > max_age_seconds:
                                file_path.unlink(missing_ok=True)
                                deleted_count += 1
                        except Exception as e:
                            logger.debug(f"Error checking file {file_path}: {e}")
            except Exception as e:
                logger.warning(f"Error sweeping temp folder {folder}: {e}")
        if deleted_count > 0:
            logger.info(f"Swept {deleted_count} expired temporary file(s).")
        return deleted_count
