import os
import gc
import time
import math
import logging
import threading
from pathlib import Path
from typing import Tuple, Optional, Callable, Dict, Any

import torch
from torch import nn
from torch.nn import functional as F
import numpy as np
from PIL import Image, ImageOps

logger = logging.getLogger("ClearPix.Upscaler")

# Ensure Apple Silicon MPS fallback is enabled for any unsupported operators
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"


class ResidualDenseBlock(nn.Module):
    """Residual Dense Block used in RRDB block in ESRGAN."""

    def __init__(self, num_feat: int = 64, num_grow_ch: int = 32):
        super().__init__()
        self.conv1 = nn.Conv2d(num_feat, num_grow_ch, 3, 1, 1)
        self.conv2 = nn.Conv2d(num_feat + num_grow_ch, num_grow_ch, 3, 1, 1)
        self.conv3 = nn.Conv2d(num_feat + 2 * num_grow_ch, num_grow_ch, 3, 1, 1)
        self.conv4 = nn.Conv2d(num_feat + 3 * num_grow_ch, num_grow_ch, 3, 1, 1)
        self.conv5 = nn.Conv2d(num_feat + 4 * num_grow_ch, num_feat, 3, 1, 1)
        self.lrelu = nn.LeakyReLU(negative_slope=0.2, inplace=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x1 = self.lrelu(self.conv1(x))
        x2 = self.lrelu(self.conv2(torch.cat((x, x1), 1)))
        x3 = self.lrelu(self.conv3(torch.cat((x, x1, x2), 1)))
        x4 = self.lrelu(self.conv4(torch.cat((x, x1, x2, x3), 1)))
        x5 = self.conv5(torch.cat((x, x1, x2, x3, x4), 1))
        return x5 * 0.2 + x


class RRDB(nn.Module):
    """Residual in Residual Dense Block used in RRDBNet."""

    def __init__(self, num_feat: int = 64, num_grow_ch: int = 32):
        super().__init__()
        self.rdb1 = ResidualDenseBlock(num_feat, num_grow_ch)
        self.rdb2 = ResidualDenseBlock(num_feat, num_grow_ch)
        self.rdb3 = ResidualDenseBlock(num_feat, num_grow_ch)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.rdb1(x)
        out = self.rdb2(out)
        out = self.rdb3(out)
        return out * 0.2 + x


class RRDBNet(nn.Module):
    """Networks consisting of Residual in Residual Dense Block, used in Real-ESRGAN x4plus."""

    def __init__(
        self,
        num_in_ch: int = 3,
        num_out_ch: int = 3,
        scale: int = 4,
        num_feat: int = 64,
        num_block: int = 23,
        num_grow_ch: int = 32,
    ):
        super().__init__()
        self.scale = scale
        self.conv_first = nn.Conv2d(num_in_ch, num_feat, 3, 1, 1)
        self.body = nn.Sequential(*[RRDB(num_feat, num_grow_ch) for _ in range(num_block)])
        self.conv_body = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        # 4x upsampling layers (2x followed by 2x)
        self.conv_up1 = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        self.conv_up2 = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        self.conv_hr = nn.Conv2d(num_feat, num_feat, 3, 1, 1)
        self.conv_last = nn.Conv2d(num_feat, num_out_ch, 3, 1, 1)
        self.lrelu = nn.LeakyReLU(negative_slope=0.2, inplace=True)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        feat = self.conv_first(x)
        body_feat = self.conv_body(self.body(feat))
        feat = feat + body_feat
        feat = self.lrelu(self.conv_up1(F.interpolate(feat, scale_factor=2, mode="nearest")))
        feat = self.lrelu(self.conv_up2(F.interpolate(feat, scale_factor=2, mode="nearest")))
        out = self.conv_last(self.lrelu(self.conv_hr(feat)))
        return out


class RealESRGANService:
    """Singleton service for Real-ESRGAN x4plus AI inference with tiled memory management and diagnostics."""

    _instance: Optional["RealESRGANService"] = None
    _init_lock = threading.Lock()

    MODEL_URL = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"
    MODEL_FILENAME = "RealESRGAN_x4plus.pth"

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    cls._instance = super(RealESRGANService, cls).__new__(cls)
        return cls._instance

    def __init__(self, models_dir: Optional[str] = None):
        if getattr(self, "_initialized", False):
            return

        with self._init_lock:
            if getattr(self, "_initialized", False):
                return

            base_dir = Path(__file__).resolve().parent.parent
            self.models_dir = Path(models_dir) if models_dir else base_dir / "models"
            self.model_path = self.models_dir / self.MODEL_FILENAME
            self.model: Optional[RRDBNet] = None
            self.model_init_time: float = 0.0
            self.timeout_seconds: float = 180.0
            self.device_name = "cpu"
            self.device = torch.device("cpu")
            self.inference_lock = threading.Lock()

            self._determine_device()
            self._ensure_model_loaded()
            self._initialized = True

    def _determine_device(self):
        """Detect and verify hardware accelerator: MPS (Apple Silicon), CUDA, or CPU."""
        logger.info(f"Checking PyTorch {torch.__version__} hardware acceleration support...")

        if torch.backends.mps.is_available():
            try:
                # Perform smoke test forward pass on MPS
                test_tensor = torch.zeros(1, 3, 16, 16, device="mps")
                test_conv = nn.Conv2d(3, 3, 3, 1, 1).to("mps")
                _ = test_conv(test_tensor)
                del test_tensor, test_conv
                torch.mps.empty_cache()

                self.device = torch.device("mps")
                self.device_name = "mps"
                logger.info("✓ Apple Silicon Metal Performance Shaders (MPS) GPU verified and active.")
            except Exception as e:
                logger.warning(f"MPS available but failed smoke test: {e}. Falling back to CPU.")
                self.device = torch.device("cpu")
                self.device_name = "cpu"
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
            self.device_name = f"cuda:{torch.cuda.current_device()}"
            logger.info(f"✓ NVIDIA CUDA GPU verified and active: {torch.cuda.get_device_name(0)}")
        else:
            self.device = torch.device("cpu")
            self.device_name = "cpu"
            logger.info("✓ Using CPU for inference.")

    def _download_model_weights(self):
        """Download pretrained RealESRGAN_x4plus.pth if missing."""
        self.models_dir.mkdir(parents=True, exist_ok=True)
        if self.model_path.exists() and self.model_path.stat().st_size > 60 * 1024 * 1024:
            logger.info(f"✓ Found model weights at {self.model_path} ({self.model_path.stat().st_size / (1024*1024):.1f} MB)")
            return

        logger.info(f"Model weights not found. Downloading RealESRGAN_x4plus from {self.MODEL_URL}...")
        import urllib.request

        temp_path = self.model_path.with_suffix(".tmp")
        try:
            req = urllib.request.Request(
                self.MODEL_URL,
                headers={"User-Agent": "Mozilla/5.0 ClearPix-RealESRGAN-Downloader/1.0"},
            )
            with urllib.request.urlopen(req) as response, open(temp_path, "wb") as out_file:
                chunk_size = 1024 * 1024
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    out_file.write(chunk)
            temp_path.replace(self.model_path)
            logger.info(f"✓ Model weights downloaded successfully ({self.model_path.stat().st_size / (1024*1024):.1f} MB).")
        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            raise RuntimeError(f"Failed to download model weights: {e}")

    def _ensure_model_loaded(self):
        """Instantiate and load RRDBNet model onto the configured device."""
        if self.model is not None:
            return

        self._download_model_weights()
        logger.info(f"Loading RealESRGAN_x4plus model from {self.model_path} onto {self.device_name}...")

        t_load_start = time.time()
        try:
            model = RRDBNet(
                num_in_ch=3,
                num_out_ch=3,
                scale=4,
                num_feat=64,
                num_block=23,
                num_grow_ch=32,
            )

            checkpoint = torch.load(str(self.model_path), map_location="cpu", weights_only=False)
            if isinstance(checkpoint, dict):
                if "params_ema" in checkpoint:
                    state_dict = checkpoint["params_ema"]
                elif "params" in checkpoint:
                    state_dict = checkpoint["params"]
                else:
                    state_dict = checkpoint
            else:
                state_dict = checkpoint

            model.load_state_dict(state_dict, strict=True)
            model.eval()
            model.to(self.device)
            self.model = model
            self.model_init_time = time.time() - t_load_start
            logger.info(f"✓ RealESRGAN_x4plus model weights loaded in {self.model_init_time:.2f}s and model set to eval mode.")
        except Exception as e:
            logger.exception("Failed to load RealESRGAN_x4plus model")
            raise RuntimeError(f"Model initialization failed: {e}")

    def is_loaded(self) -> bool:
        return self.model is not None

    def get_memory_stats(self) -> Dict[str, Any]:
        """Measure current process RSS and hardware accelerator allocated memory."""
        import resource
        import sys

        stats = {
            "device": self.device_name,
            "peak_rss_mb": 0.0,
            "mps_allocated_mb": 0.0,
            "mps_driver_mb": 0.0,
        }

        try:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            # macOS returns bytes; Linux returns kilobytes
            rss_bytes = usage.ru_maxrss if sys.platform == "darwin" else usage.ru_maxrss * 1024
            stats["peak_rss_mb"] = round(rss_bytes / (1024 * 1024), 2)
        except Exception:
            pass

        if self.device_name == "mps":
            try:
                if hasattr(torch, "mps") and hasattr(torch.mps, "current_allocated_memory"):
                    stats["mps_allocated_mb"] = round(torch.mps.current_allocated_memory() / (1024 * 1024), 2)
                if hasattr(torch, "mps") and hasattr(torch.mps, "driver_allocated_memory"):
                    stats["mps_driver_mb"] = round(torch.mps.driver_allocated_memory() / (1024 * 1024), 2)
            except Exception:
                pass
        elif "cuda" in self.device_name and torch.cuda.is_available():
            try:
                stats["cuda_allocated_mb"] = round(torch.cuda.max_memory_allocated() / (1024 * 1024), 2)
            except Exception:
                pass

        return stats

    def get_status(self) -> dict:
        return {
            "model_name": "RealESRGAN_x4plus",
            "model_loaded": self.is_loaded(),
            "model_init_seconds": round(getattr(self, "model_init_time", 0.0), 3),
            "device": self.device_name,
            "architecture": "RRDBNet (num_feat=64, num_block=23, scale=4)",
            "memory": self.get_memory_stats(),
        }

    def _clear_cache(self):
        """Release cached memory after inference."""
        if self.device_name == "mps":
            try:
                if hasattr(torch, "mps") and hasattr(torch.mps, "empty_cache"):
                    torch.mps.empty_cache()
            except Exception:
                pass
        elif "cuda" in self.device_name:
            try:
                torch.cuda.empty_cache()
            except Exception:
                pass
        gc.collect()

    def _tile_process(
        self,
        img_tensor: torch.Tensor,
        tile_size: int = 512,
        tile_pad: int = 10,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> torch.Tensor:
        """
        Run tiled inference over large images to prevent out-of-memory errors on Apple Silicon / CPU.
        Output tiles are streamed directly to CPU memory to keep GPU VRAM consumption minimal.
        """
        batch, channel, height, width = img_tensor.shape
        scale = 4

        # If image fits in one tile, run direct inference and move result to CPU
        if height <= tile_size and width <= tile_size:
            logger.info(f"Image ({width}x{height}) fits within tile size ({tile_size}px). Running single-pass inference.")
            t0 = time.time()
            res = self.model(img_tensor).cpu()
            logger.info(f"Single-pass inference finished in {time.time() - t0:.2f}s.")
            self._clear_cache()
            return res

        output_height = height * scale
        output_width = width * scale
        # Allocate output tensor on CPU to prevent holding full image in MPS Metal VRAM
        output_tensor = torch.zeros(
            (batch, channel, output_height, output_width),
            dtype=torch.float32,
            device="cpu",
        )

        tiles_x = math.ceil(width / tile_size)
        tiles_y = math.ceil(height / tile_size)
        total_tiles = tiles_x * tiles_y

        logger.info(
            f"Image ({width}x{height}) exceeds tile size ({tile_size}px). "
            f"Dividing into {total_tiles} tiles ({tiles_x} columns × {tiles_y} rows) with {tile_pad}px padding."
        )

        tile_idx = 0
        t_start = time.time()

        for y in range(tiles_y):
            for x in range(tiles_x):
                if time.time() - t_start > self.timeout_seconds:
                    raise TimeoutError(
                        f"AI enhancement exceeded maximum processing time limit of {self.timeout_seconds:.0f} seconds."
                    )
                tile_idx += 1
                t_tile_start = time.time()

                # Calculate tile input coordinates
                ofs_x = x * tile_size
                ofs_y = y * tile_size

                input_start_x = ofs_x
                input_end_x = min(ofs_x + tile_size, width)
                input_start_y = ofs_y
                input_end_y = min(ofs_y + tile_size, height)

                # Input tile with padding
                input_start_x_pad = max(input_start_x - tile_pad, 0)
                input_end_x_pad = min(input_end_x + tile_pad, width)
                input_start_y_pad = max(input_start_y - tile_pad, 0)
                input_end_y_pad = min(input_end_y + tile_pad, height)

                # Slice input tile and ensure it is on device
                input_tile = img_tensor[
                    :, :, input_start_y_pad:input_end_y_pad, input_start_x_pad:input_end_x_pad
                ]

                # Run inference on tile and immediately transfer output to CPU
                output_tile = self.model(input_tile).cpu()

                # Calculate corresponding output coordinates without padding
                output_start_x = input_start_x * scale
                output_end_x = input_end_x * scale
                output_start_y = input_start_y * scale
                output_end_y = input_end_y * scale

                # Slice boundaries for unpadded output tile
                tile_start_x = (input_start_x - input_start_x_pad) * scale
                tile_end_x = tile_start_x + (input_end_x - input_start_x) * scale
                tile_start_y = (input_start_y - input_start_y_pad) * scale
                tile_end_y = tile_start_y + (input_end_y - input_start_y) * scale

                output_tensor[:, :, output_start_y:output_end_y, output_start_x:output_end_x] = output_tile[
                    :, :, tile_start_y:tile_end_y, tile_start_x:tile_end_x
                ]

                tile_dur = time.time() - t_tile_start
                logger.info(
                    f"  Tile {tile_idx}/{total_tiles} (row {y+1}, col {x+1}) processed in {tile_dur:.2f}s "
                    f"[{output_end_x - output_start_x}x{output_end_y - output_start_y}px]"
                )

                if progress_callback:
                    try:
                        progress_callback(tile_idx, total_tiles)
                    except Exception:
                        pass

                # Release intermediate tile memory immediately
                del input_tile
                del output_tile
                self._clear_cache()

        total_tile_dur = time.time() - t_start
        logger.info(f"All {total_tiles} tiles successfully assembled in {total_tile_dur:.2f}s.")
        return output_tensor

    def enhance(
        self,
        pil_image: Image.Image,
        scale: int = 4,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Tuple[Image.Image, int, int, float]:
        """
        Enhance a PIL Image using the RealESRGAN_x4plus AI model.
        
        Args:
            pil_image: PIL Image in RGB, RGBA, L, or CMYK format
            scale: Desired output scale (2 or 4)
            progress_callback: Optional callback(current_tile, total_tiles)
            
        Returns:
            Tuple of (enhanced_pil_image, output_width, output_height, inference_duration_seconds)
        """
        if not self.is_loaded():
            self._ensure_model_loaded()

        if scale not in (2, 4):
            raise ValueError(f"Unsupported scale {scale}. Only 2x and 4x scales are supported.")

        start_time = time.time()

        # Respect EXIF orientation tag
        pil_image = ImageOps.exif_transpose(pil_image)

        orig_w, orig_h = pil_image.size
        logger.info(f"Starting enhancement: image size={orig_w}x{orig_h}, mode={pil_image.mode}, target_scale={scale}x")

        has_alpha = pil_image.mode in ("RGBA", "LA") or (
            pil_image.mode == "P" and "transparency" in pil_image.info
        )

        alpha_channel: Optional[Image.Image] = None
        if has_alpha:
            logger.info("Image contains transparency channel. Extracting alpha mask for separate preservation.")
            pil_image = pil_image.convert("RGBA")
            r, g, b, a = pil_image.split()
            rgb_image = Image.merge("RGB", (r, g, b))
            alpha_channel = a
        else:
            rgb_image = pil_image.convert("RGB")

        # Convert RGB image to normalized float32 tensor in range [0, 1]
        img_np = np.array(rgb_image, dtype=np.float32) / 255.0
        # Shape: (1, 3, H, W)
        img_tensor = (
            torch.from_numpy(np.transpose(img_np, (2, 0, 1)))
            .float()
            .unsqueeze(0)
            .to(self.device)
        )

        # Thread-safe serialized GPU execution to prevent OOM spikes
        with self.inference_lock:
            with torch.inference_mode():
                out_tensor = self._tile_process(
                    img_tensor, tile_size=512, tile_pad=10, progress_callback=progress_callback
                )

        # Convert output tensor (already on CPU) back to uint8 numpy array in range [0, 255]
        out_np = out_tensor.squeeze(0).clamp(0, 1).numpy()
        out_np = np.transpose(out_np, (1, 2, 0))
        out_np = (out_np * 255.0).round().astype(np.uint8)
        enhanced_rgb = Image.fromarray(out_np)

        # Recompose transparency if original was RGBA
        if alpha_channel is not None:
            logger.info("Resizing alpha mask with Lanczos interpolation and recomposing RGBA output.")
            enhanced_alpha = alpha_channel.resize(
                (enhanced_rgb.width, enhanced_rgb.height), resample=Image.Resampling.LANCZOS
            )
            r, g, b = enhanced_rgb.split()
            enhanced_image = Image.merge("RGBA", (r, g, b, enhanced_alpha))
        else:
            enhanced_image = enhanced_rgb

        # If 2x scale was requested, downscale the 4x super-resolved output using Lanczos
        if scale == 2:
            target_w = orig_w * 2
            target_h = orig_h * 2
            logger.info(f"Downscaling 4x output to requested 2x scale ({target_w}x{target_h}) via Lanczos.")
            enhanced_image = enhanced_image.resize(
                (target_w, target_h), resample=Image.Resampling.LANCZOS
            )

        duration = time.time() - start_time
        mem_stats = self.get_memory_stats()
        self._clear_cache()

        final_w, final_h = enhanced_image.size
        logger.info(
            f"✓ Enhancement complete: {orig_w}x{orig_h} -> {final_w}x{final_h} ({scale}x) in {duration:.2f}s on {self.device_name} "
            f"[Peak RSS: {mem_stats.get('peak_rss_mb', 0)} MB]"
        )
        return enhanced_image, final_w, final_h, duration
