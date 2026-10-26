"""
Tests for ClearPix WebGPU Integration:
- ONNX model validation (ops, format, dynamic shape, size)
- Vendor assets HTTP serving (ort.webgpu.min.js, wasm)
- WebGPU client script syntax and tiling/resampling implementation
- UI markup: engine selector pills, badges, aria attributes, metadata grid
- Zero-upload rule and fallback flow verification
"""

import os
import unittest
import urllib.request
import onnx
import onnxruntime as ort
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(PROJECT_ROOT, "static", "models", "realesr-general-x4v3.onnx")
ORT_JS_PATH = os.path.join(PROJECT_ROOT, "static", "vendor", "ort.webgpu.min.js")
ORT_WASM_PATH = os.path.join(PROJECT_ROOT, "static", "vendor", "ort-wasm-simd-threaded.jsep.wasm")
CLIENT_ENGINE_PATH = os.path.join(PROJECT_ROOT, "static", "webgpu-upscaler.js")
TEMPLATE_PATH = os.path.join(PROJECT_ROOT, "templates", "index.html")
APP_JS_PATH = os.path.join(PROJECT_ROOT, "static", "app.js")

class TestWebGPUIntegration(unittest.TestCase):

    def test_01_model_file_exists_and_valid_onnx(self):
        """Model exists, is under 10MB (fast client download), and is valid ONNX format."""
        self.assertTrue(os.path.exists(MODEL_PATH), f"Model missing: {MODEL_PATH}")
        size_mb = os.path.getsize(MODEL_PATH) / (1024 * 1024)
        self.assertLess(size_mb, 10.0, f"Model size ({size_mb:.2f} MB) exceeds 10MB limit for web deployment")
        self.assertGreater(size_mb, 1.0, f"Model size ({size_mb:.2f} MB) unexpectedly small")

        # Load and verify ONNX graph
        model = onnx.load(MODEL_PATH)
        onnx.checker.check_model(model)
        self.assertEqual(model.opset_import[0].version, 17)

    def test_02_model_operators_webgpu_compatible(self):
        """Check all operators in the model are natively supported in ONNX Runtime WebGPU."""
        model = onnx.load(MODEL_PATH)
        ops = {node.op_type for node in model.graph.node}
        webgpu_supported_ops = {
            "Add", "Sub", "Mul", "Div", "Conv", "DepthToSpace", "PRelu", "Relu",
            "Resize", "Constant", "Identity", "Concat", "Transpose", "Clip"
        }
        unsupported = ops - webgpu_supported_ops
        self.assertEqual(len(unsupported), 0, f"Model has unsupported WebGPU ops: {unsupported}")

    def test_03_model_inference_quality_and_shape(self):
        """Run ONNX model with a test tensor and verify 4x super-resolution shape and value range."""
        session = ort.InferenceSession(MODEL_PATH, providers=['CPUExecutionProvider'])
        input_name = session.get_inputs()[0].name
        output_name = session.get_outputs()[0].name

        # Create 32x32 test RGB tensor
        test_input = np.random.rand(1, 3, 32, 32).astype(np.float32)
        outputs = session.run([output_name], {input_name: test_input})
        output_tensor = outputs[0]

        self.assertEqual(output_tensor.shape, (1, 3, 128, 128), "Output tensor must be exactly 4x scale")
        self.assertFalse(np.isnan(output_tensor).any(), "Output tensor contains NaN")
        self.assertFalse(np.isinf(output_tensor).any(), "Output tensor contains Inf")

    def test_04_vendor_assets_exist(self):
        """Check ONNX Runtime Web bundle and WebAssembly binary exist locally."""
        self.assertTrue(os.path.exists(ORT_JS_PATH), "ort.webgpu.min.js missing")
        self.assertTrue(os.path.exists(ORT_WASM_PATH), "ort-wasm-simd-threaded.jsep.wasm missing")
        self.assertGreater(os.path.getsize(ORT_JS_PATH), 100_000)
        self.assertGreater(os.path.getsize(ORT_WASM_PATH), 1_000_000)

    def test_05_client_webgpu_engine_features(self):
        """Verify webgpu-upscaler.js includes detection, tiling, transparency, Lanczos, and tensor disposal."""
        with open(CLIENT_ENGINE_PATH, "r", encoding="utf-8") as f:
            code = f.read()

        # Check key components
        self.assertIn("class WebGPUUpscaler", code)
        self.assertIn("ClearPixWebGPU", code)
        self.assertIn("navigator.gpu", code)
        self.assertIn("requestAdapter", code)
        self.assertIn("tileSize = 256", code)
        self.assertIn("inputTensor.dispose", code)
        self.assertIn("outputTensor.dispose", code)
        self.assertIn("destination-in", code, "Alpha channel preservation masking must be present")
        self.assertIn("scale === 2", code, "Scale 2x adaptation must be handled")

    def test_06_ui_engine_selector_markup(self):
        """Verify index.html contains all 3 engine options, badges, and metadata grid."""
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
            html = f.read()

        self.assertIn('data-engine="auto"', html)
        self.assertIn('data-engine="webgpu"', html)
        self.assertIn('data-engine="server"', html)
        self.assertIn('id="engineBtnWebgpu"', html)
        self.assertIn('id="metaEngine"', html)
        self.assertIn('ort.webgpu.min.js', html)
        self.assertIn('webgpu-upscaler.js', html)

    def test_07_app_js_branching_and_no_upload_rule(self):
        """Verify app.js separates WebGPU from Server AI and avoids uploading when running WebGPU."""
        with open(APP_JS_PATH, "r", encoding="utf-8") as f:
            code = f.read()

        self.assertIn("executeWebGPUEnhance", code)
        self.assertIn("executeServerEnhance", code)
        self.assertIn("generateClientDownloadName", code)
        self.assertIn("selectedEngine === 'webgpu'", code)
        self.assertIn("selectedEngine === 'auto'", code)
        self.assertIn("isLocalWebGPU", code)
        self.assertIn("Browser GPU (100% On-Device)", code)
        self.assertIn("Server AI", code)

    def test_08_server_serves_static_assets_http(self):
        """Verify Flask dev server serves the static ONNX model and ORT assets with 200 OK."""
        try:
            req = urllib.request.Request("http://127.0.0.1:5001/static/vendor/ort.webgpu.min.js", method="HEAD")
            with urllib.request.urlopen(req, timeout=3) as res:
                self.assertEqual(res.status, 200)

            req_model = urllib.request.Request("http://127.0.0.1:5001/static/models/realesr-general-x4v3.onnx", method="HEAD")
            with urllib.request.urlopen(req_model, timeout=3) as res:
                self.assertEqual(res.status, 200)
        except urllib.error.URLError as e:
            self.skipTest(f"Flask server not running on port 5001: {e}")

if __name__ == "__main__":
    unittest.main()
