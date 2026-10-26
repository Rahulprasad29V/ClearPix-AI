"""
Test suite verifying ClearPix Real-ESRGAN enhancement quality, pipeline fidelity,
viewer DOM alignment, and comparison against baseline Lanczos resizing.
"""

import os
import sys
import unittest
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.upscaler import RealESRGANService

BENCHMARK_IMG = PROJECT_ROOT / "tests" / "benchmark_test.jpg"
SAMPLE_IMG = PROJECT_ROOT / "tests" / "sample.jpg"

class TestEnhancementQuality(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.service = RealESRGANService()

    def test_01_native_4x_dimensions_and_png_integrity(self):
        """Verify 4x output preserves exact native 4x dimensions and lossless format."""
        orig_img = Image.open(BENCHMARK_IMG)
        orig_w, orig_h = orig_img.size

        enhanced, out_w, out_h, duration = self.service.enhance(orig_img, scale=4)

        self.assertEqual(out_w, orig_w * 4, f"Expected width {orig_w * 4}, got {out_w}")
        self.assertEqual(out_h, orig_h * 4, f"Expected height {orig_h * 4}, got {out_h}")
        self.assertEqual(enhanced.size, (orig_w * 4, orig_h * 4))
        self.assertGreater(duration, 0.0)

        # Save to PNG and re-read to verify lossless roundtrip
        test_out = PROJECT_ROOT / "temp" / "quality_test_4x.png"
        test_out.parent.mkdir(parents=True, exist_ok=True)
        enhanced.save(test_out, format="PNG", optimize=True)

        reloaded = Image.open(test_out)
        self.assertEqual(reloaded.size, (out_w, out_h))
        self.assertEqual(reloaded.format, "PNG")

    def test_02_scale_2x_dimensions_and_resampling(self):
        """Verify 2x scale accurately downscales 4x output to exact 2x dimensions."""
        orig_img = Image.open(BENCHMARK_IMG)
        orig_w, orig_h = orig_img.size

        enhanced_2x, out_w, out_h, duration = self.service.enhance(orig_img, scale=2)

        self.assertEqual(out_w, orig_w * 2, f"Expected width {orig_w * 2}, got {out_w}")
        self.assertEqual(out_h, orig_h * 2, f"Expected height {orig_h * 2}, got {out_h}")
        self.assertEqual(enhanced_2x.size, (orig_w * 2, orig_h * 2))

    def test_03_quality_superior_to_lanczos_baseline(self):
        """
        Compare Real-ESRGAN high-frequency detail and edge reconstruction against
        a naive Lanczos 4x resize baseline on benchmark photo.
        """
        orig_img = Image.open(BENCHMARK_IMG)
        enhanced_4x, out_w, out_h, _ = self.service.enhance(orig_img, scale=4)
        lanczos_4x = orig_img.resize((out_w, out_h), Image.Resampling.LANCZOS)

        # High-pass filter kernel to measure high-frequency detail/sharpness
        laplacian_kernel = ImageFilter.Kernel((3, 3), [0, 1, 0, 1, -4, 1, 0, 1, 0], scale=1)
        lanczos_lap = np.array(lanczos_4x.convert("L").filter(laplacian_kernel), dtype=np.float32)
        esrgan_lap = np.array(enhanced_4x.convert("L").filter(laplacian_kernel), dtype=np.float32)

        lanczos_var = float(lanczos_lap.var())
        esrgan_var = float(esrgan_lap.var())

        print(f"\n  [Sharpness Verification]")
        print(f"  • Lanczos 4x Laplacian Variance:     {lanczos_var:.2f}")
        print(f"  • Real-ESRGAN 4x Laplacian Variance: {esrgan_var:.2f}")
        print(f"  • Detail Enhancement Factor:         {esrgan_var / lanczos_var:.2f}x")

        # Real-ESRGAN must exhibit significantly higher reconstructed edge detail than naive blur/interpolation
        self.assertGreater(
            esrgan_var,
            lanczos_var * 2.0,
            f"Real-ESRGAN output ({esrgan_var:.2f}) should be at least 2x sharper than Lanczos ({lanczos_var:.2f})",
        )

    def test_04_viewer_markup_and_alignment(self):
        """Verify templates/index.html establishes high-res in-flow canvas and correct overlay."""
        index_html_path = PROJECT_ROOT / "templates" / "index.html"
        with open(index_html_path, "r", encoding="utf-8") as f:
            html = f.read()

        # In-flow base image must be upscaledPreview
        self.assertIn('<img id="upscaledPreview" alt="AI super-resolved photo preview">', html)
        # Overlay pane must contain previewImage
        self.assertIn('<div id="beforePane" class="before-pane after-pane">', html)
        self.assertIn('<img id="previewImage" alt="Original photo preview">', html)

        # Labels must be correctly oriented: ORIGINAL on left, AI ENHANCED on right
        self.assertIn('<div class="preview-label before-label">ORIGINAL</div>', html)
        self.assertIn('<div class="preview-label after-label" id="afterBadge">AI ENHANCED 4×</div>', html)

    def test_05_viewer_css_aspect_ratio_and_object_fit(self):
        """Verify CSS ensures in-flow sizing without crushing high-res output and perfect alignment."""
        style_css_path = PROJECT_ROOT / "static" / "style.css"
        with open(style_css_path, "r", encoding="utf-8") as f:
            css = f.read()

        self.assertIn(".before-pane", css)
        self.assertIn(".after-pane", css)
        self.assertIn("object-fit: fill", css)

    def test_06_app_js_zoom_and_reveal_logic(self):
        """Verify app.js calculates true native scale, proper zoom modes, and left-to-right reveal."""
        app_js_path = PROJECT_ROOT / "static" / "app.js"
        with open(app_js_path, "r", encoding="utf-8") as f:
            js = f.read()

        self.assertIn("currentNativeScale", js)
        self.assertIn("updateNativeScale()", js)
        self.assertIn("beforePane.style.clipPath", js)
        self.assertIn("polygon(0 0, ${clamped}% 0, ${clamped}% 100%, 0 100%)", js)


if __name__ == "__main__":
    unittest.main()
