import io
import sys
import json
import unittest
import urllib.request
import urllib.error
from pathlib import Path
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

BASE_URL = "http://127.0.0.1:5001"


def multipart_post(url, fields, files):
    boundary = "----WebKitFormBoundaryUnitTest7MA4YW"
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
    return urllib.request.urlopen(req, timeout=120)


class ClearPixProductionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Verify server is reachable
        try:
            res = urllib.request.urlopen(f"{BASE_URL}/api/health", timeout=5)
            data = json.loads(res.read().decode())
            cls.device = data.get("device")
        except Exception as e:
            raise RuntimeError(f"Server is not running on {BASE_URL}: {e}")

    def test_01_health_endpoint(self):
        """Verify health check endpoint returns all production metrics."""
        res = urllib.request.urlopen(f"{BASE_URL}/api/health")
        self.assertEqual(res.status, 200)
        data = json.loads(res.read().decode())
        self.assertEqual(data["status"], "ok")
        self.assertTrue(data["model_loaded"])
        self.assertIn("model_init_seconds", data)
        self.assertIn("memory", data)
        self.assertIn(data["device"], ("mps", "cuda", "cpu"))

    def test_02_empty_file_rejected(self):
        """Verify empty file upload returns HTTP 400."""
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            multipart_post(
                f"{BASE_URL}/api/enhance",
                fields={"scale": 4},
                files={"image": ("empty.png", b"", "image/png")},
            )
        self.assertEqual(ctx.exception.code, 400)
        err = json.loads(ctx.exception.read().decode())
        self.assertEqual(err["status"], "error")

    def test_03_corrupted_file_rejected(self):
        """Verify corrupted binary image returns HTTP 400."""
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            multipart_post(
                f"{BASE_URL}/api/enhance",
                fields={"scale": 4},
                files={"image": ("corrupted.png", b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRbad_bytes", "image/png")},
            )
        self.assertEqual(ctx.exception.code, 400)

    def test_04_unsupported_formats_rejected(self):
        """Verify GIF, BMP, and TIFF formats return clear HTTP 400 errors."""
        formats = [
            ("anim.gif", b"GIF89a\x01\x00\x01\x00", "GIF images are not supported"),
            ("test.bmp", b"BM\x36\x00\x00\x00", "BMP images are not supported"),
            ("scan.tiff", b"II*\x00\x08", "TIFF images are not supported"),
        ]
        for fname, raw_bytes, expected_msg in formats:
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                multipart_post(
                    f"{BASE_URL}/api/enhance",
                    fields={"scale": 4},
                    files={"image": (fname, raw_bytes, "application/octet-stream")},
                )
            self.assertEqual(ctx.exception.code, 400)
            err = json.loads(ctx.exception.read().decode())
            self.assertIn(expected_msg, err["message"])

    def test_05_undersized_image_rejected(self):
        """Verify images smaller than 16x16px return HTTP 400."""
        buf = io.BytesIO()
        Image.new("RGB", (12, 12)).save(buf, format="PNG")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            multipart_post(
                f"{BASE_URL}/api/enhance",
                fields={"scale": 4},
                files={"image": ("tiny.png", buf.getvalue(), "image/png")},
            )
        self.assertEqual(ctx.exception.code, 400)

    def test_06_enhance_2x_scale(self):
        """Verify 2x scale super-resolution output dimensions and PNG download."""
        w, h = 60, 40
        buf = io.BytesIO()
        Image.new("RGB", (w, h), (100, 150, 200)).save(buf, format="JPEG")

        res = multipart_post(
            f"{BASE_URL}/api/enhance",
            fields={"scale": 2},
            files={"image": ("test_2x.jpg", buf.getvalue(), "image/jpeg")},
        )
        self.assertEqual(res.status, 200)
        data = json.loads(res.read().decode())
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["output_dimensions"]["width"], w * 2)
        self.assertEqual(data["output_dimensions"]["height"], h * 2)
        self.assertIn("timing", data)
        self.assertIn("memory", data)

        # Verify real PNG download
        dl_res = urllib.request.urlopen(f"{BASE_URL}{data['download_url']}")
        self.assertEqual(dl_res.status, 200)
        self.assertEqual(dl_res.headers.get("Content-Type"), "image/png")
        dl_img = Image.open(io.BytesIO(dl_res.read()))
        self.assertEqual(dl_img.size, (w * 2, h * 2))

    def test_07_enhance_4x_scale(self):
        """Verify 4x scale super-resolution output dimensions and PNG download."""
        w, h = 50, 50
        buf = io.BytesIO()
        Image.new("RGB", (w, h), (180, 100, 50)).save(buf, format="PNG")

        res = multipart_post(
            f"{BASE_URL}/api/enhance",
            fields={"scale": 4},
            files={"image": ("test_4x.png", buf.getvalue(), "image/png")},
        )
        self.assertEqual(res.status, 200)
        data = json.loads(res.read().decode())
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["output_dimensions"]["width"], w * 4)
        self.assertEqual(data["output_dimensions"]["height"], h * 4)

        # Verify real PNG download
        dl_res = urllib.request.urlopen(f"{BASE_URL}{data['download_url']}")
        self.assertEqual(dl_res.status, 200)
        dl_img = Image.open(io.BytesIO(dl_res.read()))
        self.assertEqual(dl_img.size, (w * 4, h * 4))

    def test_08_rgba_transparency_preserved(self):
        """Verify RGBA transparency channel is preserved in the enhanced PNG."""
        w, h = 60, 60
        rgba_img = Image.new("RGBA", (w, h), (100, 120, 200, 128))
        buf = io.BytesIO()
        rgba_img.save(buf, format="PNG")

        res = multipart_post(
            f"{BASE_URL}/api/enhance",
            fields={"scale": 4},
            files={"image": ("alpha.png", buf.getvalue(), "image/png")},
        )
        self.assertEqual(res.status, 200)
        data = json.loads(res.read().decode())
        dl_res = urllib.request.urlopen(f"{BASE_URL}{data['download_url']}")
        dl_img = Image.open(io.BytesIO(dl_res.read()))
        self.assertEqual(dl_img.mode, "RGBA")
        self.assertEqual(dl_img.size, (w * 4, h * 4))

    def test_09_temp_file_cleanup(self):
        """Verify TempFileManager cleans expired temporary files."""
        from utils.image_utils import TempFileManager
        mgr = TempFileManager()
        test_id = mgr.generate_id()
        saved = mgr.save_output(test_id, Image.new("RGB", (20, 20)))
        self.assertTrue(saved.exists())
        mgr.cleanup_expired(max_age_seconds=0)
        self.assertFalse(saved.exists())

    def test_10_footer_cyberwolf_attribution(self):
        """Verify exact footer attribution, author name, bold Branch Head (India), CyberWolf team link, target, and rel."""
        res = urllib.request.urlopen(f"{BASE_URL}/")
        self.assertEqual(res.status, 200)
        html = res.read().decode("utf-8")
        self.assertIn("Made by <strong>Rahulprasad Veeramani</strong>", html)
        self.assertIn("Branch Head (India)", html)
        self.assertIn("https://www.cyberwolf360.in/", html)
        self.assertIn('target="_blank"', html)
        self.assertIn('rel="noopener noreferrer"', html)
        self.assertIn("CyberWolf Team", html)

    def test_11_seo_and_creator_visibility(self):
        """Verify SEO metadata, title, Person JSON-LD, About the Creator section, robots.txt, and sitemap.xml."""
        # 1. Check home page HTML metadata & visible sections
        res = urllib.request.urlopen(f"{BASE_URL}/")
        self.assertEqual(res.status, 200)
        html = res.read().decode("utf-8")
        self.assertIn("<title>ClearPix — Cross-Platform AI Photo Enhancer | Rahulprasad Veeramani</title>", html)
        self.assertIn("name=\"description\"", html)
        self.assertIn("Rahulprasad Veeramani", html)
        self.assertIn("Branch Head (India) @ CyberWolf Team", html)
        self.assertIn('id="creator"', html)
        self.assertIn("About the Creator", html)
        self.assertIn("og:image", html)
        self.assertIn("static/og-preview.png", html)
        self.assertIn('href="/privacy"', html)
        self.assertIn("Use ClearPix on your phone, tablet, or computer", html)
        # Check Person schema in JSON-LD
        self.assertIn('"@type": "Person"', html)
        self.assertIn('"name": "Rahulprasad Veeramani"', html)
        self.assertIn('"jobTitle": "Branch Head (India)"', html)
        self.assertNotIn("noindex", html.lower())

        # 2. Check crawlable robots.txt
        res_robots = urllib.request.urlopen(f"{BASE_URL}/robots.txt")
        self.assertEqual(res_robots.status, 200)
        robots_txt = res_robots.read().decode("utf-8")
        self.assertIn("User-agent: *", robots_txt)
        self.assertIn("Allow: /", robots_txt)
        self.assertIn("sitemap.xml", robots_txt)

        # 3. Check sitemap.xml
        res_sitemap = urllib.request.urlopen(f"{BASE_URL}/sitemap.xml")
        self.assertEqual(res_sitemap.status, 200)
        sitemap_xml = res_sitemap.read().decode("utf-8")
        self.assertIn("<urlset", sitemap_xml)
        self.assertIn("<loc>", sitemap_xml)
        self.assertIn("/privacy</loc>", sitemap_xml)

    def test_12_privacy_policy_page(self):
        """Verify /privacy route loads directly, has accurate content, operator info, and theme toggle."""
        res = urllib.request.urlopen(f"{BASE_URL}/privacy")
        self.assertEqual(res.status, 200)
        html = res.read().decode("utf-8")
        self.assertIn("<title>Privacy Policy — ClearPix AI Photo Enhancer</title>", html)
        self.assertIn("ClearPix Privacy Policy", html)
        self.assertIn("Rahulprasad Veeramani", html)
        self.assertIn("Branch Head (India) @ CyberWolf Team", html)
        self.assertIn("https://www.cyberwolf360.in/", html)
        self.assertIn("privacy@cyberwolf360.in", html)
        self.assertIn("3,600 seconds", html)
        self.assertIn("1 hour", html)
        self.assertIn("Server-Side AI", html)
        self.assertIn("Zero AI Model Training", html)
        self.assertIn("No Tracking Cookies", html)
        self.assertIn("themeToggleBtn", html)
        self.assertNotIn("noindex", html.lower())

    def test_13_upscaler_service_enhance_tuple_contract(self):
        """Verify RealESRGANService.enhance returns exactly 4 values: (enhanced_image, out_w, out_h, duration)."""
        from services.upscaler import RealESRGANService
        service = RealESRGANService()
        test_img = Image.new("RGB", (32, 32), color=(100, 150, 200))
        res = service.enhance(test_img, scale=2)
        self.assertIsInstance(res, tuple)
        self.assertEqual(len(res), 4, f"Expected 4-tuple, got {len(res)} items")
        enhanced_img, out_w, out_h, duration = res
        self.assertIsInstance(enhanced_img, Image.Image)
        self.assertEqual((out_w, out_h), (64, 64))
        self.assertEqual(enhanced_img.size, (64, 64))
        self.assertIsInstance(duration, float)
        self.assertGreater(duration, 0.0)


if __name__ == "__main__":
    unittest.main()
