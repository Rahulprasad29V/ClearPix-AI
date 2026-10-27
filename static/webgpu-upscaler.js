/**
 * ClearPix Client-Side WebGPU Super-Resolution Engine
 * Powered by ONNX Runtime Web (WebGPU execution provider)
 * Model: Real-ESRGAN Compact x4v3 (SRVGGNetCompact)
 * License: BSD 3-Clause (Open Source)
 */

(function(global) {
  'use strict';

  class WebGPUUpscaler {
    constructor() {
      this.modelPath = '/static/models/realesr-general-x4v3.onnx';
      this.session = null;
      this.isModelLoading = false;
      this.loadPromise = null;
      this.isDeviceSupported = false;
      this.adapterInfo = null;
      this.gpuDevice = null;
      this.activeJobAbortController = null;
    }

    /**
     * Safely probe for WebGPU availability and hardware capabilities.
     * Handles unsupported browsers, disabled flags, and hardware initialization errors.
     */
    async checkSupport() {
      if (typeof navigator === 'undefined' || !navigator.gpu) {
        this.isDeviceSupported = false;
        return {
          supported: false,
          reason: 'WebGPU is not supported in this browser (Chrome 113+, Edge 113+, or Safari 18+ with WebGPU enabled required).'
        };
      }

      try {
        const adapter = await navigator.gpu.requestAdapter({
          powerPreference: 'high-performance'
        });

        if (!adapter) {
          this.isDeviceSupported = false;
          return {
            supported: false,
            reason: 'No compatible WebGPU hardware graphics adapter found.'
          };
        }

        // Check adapter details
        const info = adapter.info || {};
        const adapterName = info.description || info.device || info.architecture || 'Hardware GPU';
        const vendor = info.vendor || '';

        // Safely test device acquisition
        const device = await adapter.requestDevice();
        if (device && typeof device.destroy === 'function') {
          device.destroy();
        }

        this.isDeviceSupported = true;
        this.adapterInfo = {
          name: adapterName,
          vendor: vendor,
          maxBufferSize: adapter.limits ? adapter.limits.maxBufferSize : null,
          maxStorageBufferBindingSize: adapter.limits ? adapter.limits.maxStorageBufferBindingSize : null,
        };

        return {
          supported: true,
          adapterName: adapterName,
          vendor: vendor
        };
      } catch (err) {
        this.isDeviceSupported = false;
        console.warn('[WebGPU] Feature probe failed:', err);
        return {
          supported: false,
          reason: `WebGPU initialization failed: ${err.message || err}`
        };
      }
    }

    /**
     * Initialize ONNX Runtime Web with WebGPU Execution Provider.
     */
    async loadModel(onProgress) {
      if (this.session) return this.session;
      if (this.isModelLoading && this.loadPromise) return this.loadPromise;

      this.isModelLoading = true;
      this.loadPromise = (async () => {
        if (typeof global.ort === 'undefined') {
          throw new Error('ONNX Runtime Web library (ort.webgpu) is not loaded.');
        }

        const ort = global.ort;

        // Configure ONNX Runtime wasm paths
        try {
          if (ort.env && ort.env.wasm) {
            ort.env.wasm.wasmPaths = '/static/vendor/';
            ort.env.wasm.numThreads = typeof navigator !== 'undefined' && navigator.hardwareConcurrency
              ? Math.min(4, navigator.hardwareConcurrency)
              : 2;
            ort.env.wasm.proxy = false;
          }
        } catch (e) {
          console.debug('[WebGPU] Wasm path config fallback:', e);
        }

        if (onProgress) onProgress(0.1, 'Loading WebGPU Real-ESRGAN Compact model (4.8 MB)...');

        // Session creation options preferring WebGPU
        const sessionOptions = {
          executionProviders: ['webgpu', 'wasm'],
          graphOptimizationLevel: 'all',
          enableCpuMemArena: true,
          enableMemPattern: true
        };

        try {
          console.info(`[WebGPU] Instantiating ONNX session for ${this.modelPath}...`);
          this.session = await ort.InferenceSession.create(this.modelPath, sessionOptions);
          if (onProgress) onProgress(1.0, 'WebGPU model loaded and compiled.');
          console.info('[WebGPU] Model compiled successfully with providers:', sessionOptions.executionProviders);
          return this.session;
        } catch (err) {
          console.error('[WebGPU] Failed to compile ONNX model on WebGPU:', err);
          throw new Error(`Failed to load WebGPU model: ${err.message || err}`);
        } finally {
          this.isModelLoading = false;
        }
      })();

      return this.loadPromise;
    }

    /**
     * Perform real client-side AI image super-resolution.
     * 
     * @param {File|Blob|HTMLImageElement|ImageBitmap} inputSource 
     * @param {number} scale 2 or 4
     * @param {Function} progressCallback (pct, stageName)
     * @returns {Promise<{blob: Blob, width: number, height: number, durationSeconds: number, deviceName: string, engineName: string}>}
     */
    async enhance(inputSource, scale = 4, progressCallback = null, abortSignal = null) {
      if (![2, 4].includes(scale)) {
        throw new Error(`Unsupported scale factor ${scale}. Only 2× and 4× are supported.`);
      }

      const tStart = performance.now();
      const ort = global.ort;
      if (!ort) {
        throw new Error('ONNX Runtime Web is unavailable in this environment.');
      }

      // Step 1: Ensure session is ready
      if (!this.session) {
        if (progressCallback) progressCallback(0.05, 'Initializing WebGPU shader pipeline...');
        await this.loadModel(progressCallback);
      }

      // Step 2: Load and decode image to an offscreen Canvas
      if (progressCallback) progressCallback(0.15, 'Decoding image in browser memory...');
      const { canvas: inputCanvas, ctx: inputCtx, width: origW, height: origH, hasAlpha } =
        await this._decodeToCanvas(inputSource);

      if (origW < 16 || origH < 16) {
        throw new Error(`Image dimensions (${origW}×${origH}) are too small. Minimum required is 16×16 px.`);
      }
      if (origW > 4096 || origH > 4096 || (origW * origH) > 16000000) {
        throw new Error(`Image size (${origW}×${origH} px) exceeds browser limits (max 4096×4096 px / 16 MP).`);
      }

      // Extract image data
      const imgData = inputCtx.getImageData(0, 0, origW, origH);
      const rgba = imgData.data;

      // Extract alpha mask if image has transparency
      let alphaCanvas = null;
      if (hasAlpha) {
        alphaCanvas = this._extractAlphaCanvas(rgba, origW, origH);
      }

      // Step 3: Tiled Super-Resolution
      // Tile size of 256 or 512 avoids WebGPU device memory limits on mobile GPUs
      const tileSize = 256;
      const tilePad = 8;
      const netScale = 4; // Native model scale is 4x

      const outW4x = origW * netScale;
      const outH4x = origH * netScale;

      const outputCanvas4x = document.createElement('canvas');
      outputCanvas4x.width = outW4x;
      outputCanvas4x.height = outH4x;
      const outCtx4x = outputCanvas4x.getContext('2d', { willReadFrequently: true });

      // Compute tile grid
      const cols = Math.ceil(origW / tileSize);
      const rows = Math.ceil(origH / tileSize);
      const totalTiles = cols * rows;

      console.info(`[WebGPU] Processing ${origW}×${origH} image in ${totalTiles} tiles (${cols}×${rows}) on WebGPU...`);

      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          if (abortSignal && abortSignal.aborted) {
            const abortErr = new Error('Enhancement was cancelled by user.');
            abortErr.name = 'AbortError';
            throw abortErr;
          }

          const tileIndex = r * cols + c + 1;
          const pct = 0.2 + (tileIndex / totalTiles) * 0.7;
          if (progressCallback) {
            progressCallback(pct, `Running WebGPU inference: tile ${tileIndex}/${totalTiles}...`);
          }

          // Tile input bounds
          const x0 = c * tileSize;
          const y0 = r * tileSize;
          const x1 = Math.min(x0 + tileSize, origW);
          const y1 = Math.min(y0 + tileSize, origH);

          // Padded bounds
          const px0 = Math.max(0, x0 - tilePad);
          const py0 = Math.max(0, y0 - tilePad);
          const px1 = Math.min(origW, x1 + tilePad);
          const py1 = Math.min(origH, y1 + tilePad);

          const curPadW = px1 - px0;
          const curPadH = py1 - py0;

          // Extract tile RGB to NCHW float32 tensor in range [0, 1]
          const float32Data = new Float32Array(1 * 3 * curPadH * curPadW);
          const channelSize = curPadH * curPadW;

          let pIdx = 0;
          for (let y = py0; y < py1; y++) {
            for (let x = px0; x < px1; x++) {
              const srcIdx = (y * origW + x) * 4;
              float32Data[pIdx] = rgba[srcIdx] / 255.0; // R
              float32Data[channelSize + pIdx] = rgba[srcIdx + 1] / 255.0; // G
              float32Data[channelSize * 2 + pIdx] = rgba[srcIdx + 2] / 255.0; // B
              pIdx++;
            }
          }

          const inputTensor = new ort.Tensor('float32', float32Data, [1, 3, curPadH, curPadW]);
          let outputTensor = null;

          try {
            const feeds = { [this.session.inputNames[0]]: inputTensor };
            const results = await this.session.run(feeds);
            outputTensor = results[this.session.outputNames[0]];

            // Extract output tile pixels
            const outPadW = curPadW * netScale;
            const outPadH = curPadH * netScale;
            const outData = outputTensor.data;
            const outChannelSize = outPadH * outPadW;

            // Crop padding from output
            const padLeft = (x0 - px0) * netScale;
            const padTop = (y0 - py0) * netScale;
            const cropW = (x1 - x0) * netScale;
            const cropH = (y1 - y0) * netScale;

            const tileImgData = outCtx4x.createImageData(cropW, cropH);
            const tileRgba = tileImgData.data;

            let destIdx = 0;
            for (let ty = 0; ty < cropH; ty++) {
              const srcY = padTop + ty;
              for (let tx = 0; tx < cropW; tx++) {
                const srcX = padLeft + tx;
                const srcIdx = srcY * outPadW + srcX;

                const rVal = Math.round(Math.max(0, Math.min(1, outData[srcIdx])) * 255);
                const gVal = Math.round(Math.max(0, Math.min(1, outData[outChannelSize + srcIdx])) * 255);
                const bVal = Math.round(Math.max(0, Math.min(1, outData[outChannelSize * 2 + srcIdx])) * 255);

                tileRgba[destIdx] = rVal;
                tileRgba[destIdx + 1] = gVal;
                tileRgba[destIdx + 2] = bVal;
                tileRgba[destIdx + 3] = 255;
                destIdx += 4;
              }
            }

            // Write tile into main 4x canvas
            outCtx4x.putImageData(tileImgData, x0 * netScale, y0 * netScale);

          } finally {
            // Free GPU buffers immediately
            if (inputTensor && typeof inputTensor.dispose === 'function') {
              inputTensor.dispose();
            }
            if (outputTensor && typeof outputTensor.dispose === 'function') {
              outputTensor.dispose();
            }
          }
        }
      }

      // Step 4: Recompose Alpha Channel if original had transparency
      if (hasAlpha && alphaCanvas) {
        if (progressCallback) progressCallback(0.92, 'Preserving alpha transparency channel...');
        const alpha4x = document.createElement('canvas');
        alpha4x.width = outW4x;
        alpha4x.height = outH4x;
        const alpha4xCtx = alpha4x.getContext('2d');
        alpha4xCtx.imageSmoothingEnabled = true;
        alpha4xCtx.imageSmoothingQuality = 'high';
        alpha4xCtx.drawImage(alphaCanvas, 0, 0, outW4x, outH4x);

        outCtx4x.globalCompositeOperation = 'destination-in';
        outCtx4x.drawImage(alpha4x, 0, 0);
        outCtx4x.globalCompositeOperation = 'source-over';
      }

      // Step 5: Scale Adaptation (4x or 2x)
      let finalCanvas = outputCanvas4x;
      let finalW = outW4x;
      let finalH = outH4x;

      if (scale === 2) {
        if (progressCallback) progressCallback(0.95, 'Downscaling to requested 2× resolution via high-quality resampling...');
        finalW = origW * 2;
        finalH = origH * 2;
        const canvas2x = document.createElement('canvas');
        canvas2x.width = finalW;
        canvas2x.height = finalH;
        const ctx2x = canvas2x.getContext('2d');
        ctx2x.imageSmoothingEnabled = true;
        ctx2x.imageSmoothingQuality = 'high';
        ctx2x.drawImage(outputCanvas4x, 0, 0, finalW, finalH);
        finalCanvas = canvas2x;
      }

      if (progressCallback) progressCallback(0.98, 'Packaging lossless PNG result...');

      // Convert final canvas to PNG Blob
      const blob = await new Promise((resolve, reject) => {
        finalCanvas.toBlob((b) => {
          if (b) resolve(b);
          else reject(new Error('Canvas toBlob conversion failed.'));
        }, 'image/png');
      });

      const durationSeconds = (performance.now() - tStart) / 1000.0;
      const deviceName = (this.adapterInfo && this.adapterInfo.name) ? this.adapterInfo.name : 'WebGPU Hardware';

      console.info(
        `[WebGPU] ✓ In-browser super-resolution complete: ${origW}×${origH} -> ${finalW}×${finalH} (${scale}×) ` +
        `in ${durationSeconds.toFixed(2)}s on ${deviceName}.`
      );

      return {
        blob: blob,
        width: finalW,
        height: finalH,
        durationSeconds: durationSeconds,
        deviceName: deviceName,
        engineName: 'Browser WebGPU (ONNX Real-ESRGAN Compact)',
        isLocalWebGPU: true
      };
    }

    /**
     * Decode an input source to HTML Canvas and check for genuine alpha channel.
     */
    async _decodeToCanvas(inputSource) {
      let imgBitmap;
      if (inputSource instanceof HTMLImageElement) {
        imgBitmap = await createImageBitmap(inputSource);
      } else if (inputSource instanceof Blob || inputSource instanceof File) {
        imgBitmap = await createImageBitmap(inputSource);
      } else if (typeof ImageBitmap !== 'undefined' && inputSource instanceof ImageBitmap) {
        imgBitmap = inputSource;
      } else {
        throw new Error('Unsupported image input type for WebGPU enhancement.');
      }

      const canvas = document.createElement('canvas');
      canvas.width = imgBitmap.width;
      canvas.height = imgBitmap.height;
      const ctx = canvas.getContext('2d', { willReadFrequently: true });
      ctx.drawImage(imgBitmap, 0, 0);

      const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
      const data = imgData.data;

      // Check if any pixels have alpha < 255
      let hasAlpha = false;
      for (let i = 3; i < data.length; i += 4) {
        if (data[i] < 255) {
          hasAlpha = true;
          break;
        }
      }

      return {
        canvas,
        ctx,
        width: canvas.width,
        height: canvas.height,
        hasAlpha
      };
    }

    /**
     * Extract alpha mask to a separate grayscale canvas for smooth resampling.
     */
    _extractAlphaCanvas(rgba, width, height) {
      const alphaCanvas = document.createElement('canvas');
      alphaCanvas.width = width;
      alphaCanvas.height = height;
      const alphaCtx = alphaCanvas.getContext('2d');
      const alphaImgData = alphaCtx.createImageData(width, height);
      const alphaData = alphaImgData.data;

      for (let i = 0; i < rgba.length; i += 4) {
        const a = rgba[i + 3];
        alphaData[i] = a;
        alphaData[i + 1] = a;
        alphaData[i + 2] = a;
        alphaData[i + 3] = 255;
      }

      alphaCtx.putImageData(alphaImgData, 0, 0);
      return alphaCanvas;
    }
  }

  // Export singleton instance
  global.ClearPixWebGPU = new WebGPUUpscaler();

})(typeof window !== 'undefined' ? window : this);
