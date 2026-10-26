// ClearPix AI Photo Upscaler Client — Production Engine with 3D Effects & Loading Experience

// DOM Elements - Navigation & Dropzone
const input = document.querySelector('#fileInput');
const dropzone = document.querySelector('#dropzone');
const browseBtn = document.querySelector('#browseBtn');
const deviceText = document.querySelector('#deviceText');
const mobileDeviceText = document.querySelector('#mobileDeviceText');
const mobileMenuBtn = document.querySelector('#mobileMenuBtn');
const mobileDrawer = document.querySelector('#mobileDrawer');
const mobileDrawerBackdrop = document.querySelector('#mobileDrawerBackdrop');
const mobileNavItems = document.querySelectorAll('.mobile-nav-item');

// Config Card Elements
const configCard = document.querySelector('#configCard');
const configFileName = document.querySelector('#configFileName');
const configThumbnail = document.querySelector('#configThumbnail');
const configFileMeta = document.querySelector('#configFileMeta');
const configOutputMeta = document.querySelector('#configOutputMeta');
const cancelSelectBtn = document.querySelector('#cancelSelectBtn');
const scalePills = document.querySelectorAll('.scale-pill');
const enhanceBtn = document.querySelector('#enhanceBtn');
const cancelEnhanceBtn = document.querySelector('#cancelEnhanceBtn');
const btnSpinner = document.querySelector('#btnSpinner');
const btnText = document.querySelector('#btnText');
const progressWrap = document.querySelector('#progressWrap');
const progressStatus = document.querySelector('#progressStatus');
const progressBar = document.querySelector('#progressBar');
const elapsedTimer = document.querySelector('#elapsedTimer');
const errorBanner = document.querySelector('#errorBanner');
const errorMessage = document.querySelector('#errorMessage');
const retryBtn = document.querySelector('#retryBtn');

// Dedicated 3D Processing Screen Elements
const processingScreen = document.querySelector('#processingScreen');
const procHologramImg = document.querySelector('#procHologramImg');
const procDeviceText = document.querySelector('#procDeviceText');
const procStatusTitle = document.querySelector('#procStatusTitle');
const procStatusDesc = document.querySelector('#procStatusDesc');
const procTimerVal = document.querySelector('#procTimerVal');
const procScaleText = document.querySelector('#procScaleText');
const procCancelBtn = document.querySelector('#procCancelBtn');
const pStage1 = document.querySelector('#pStage1');
const pStage2 = document.querySelector('#pStage2');
const pStage3 = document.querySelector('#pStage3');
const pStage4 = document.querySelector('#pStage4');
const pStage5 = document.querySelector('#pStage5');
const procSteps = [pStage1, pStage2, pStage3, pStage4, pStage5];

// Editor & Comparison Elements
const editor = document.querySelector('#editor');
const previewStage = document.querySelector('#previewStage');
const previewWrap = document.querySelector('#previewWrap');
const original = document.querySelector('#previewImage');
const enlarged = document.querySelector('#upscaledPreview');
const beforePane = document.querySelector('#beforePane') || document.querySelector('#afterPane');
const afterPane = beforePane;
const afterBadge = document.querySelector('#afterBadge');
const slider = document.querySelector('#compareSlider');
const sliderLine = document.querySelector('#sliderLine');
const fileNameEl = document.querySelector('#fileName');
const dimensionsEl = document.querySelector('#dimensions');
const outputDimensionsEl = document.querySelector('#outputDimensions');
const downloadBtn = document.querySelector('#downloadBtn');
const resetBtn = document.querySelector('#resetBtn');
const status = document.querySelector('#status');
const beforeLabel = document.querySelector('.before-label');
const afterLabel = document.querySelector('.after-label');

// Zoom & Metadata Elements
const zoomInBtn = document.querySelector('#zoomInBtn');
const zoomOutBtn = document.querySelector('#zoomOutBtn');
const zoomLevelEl = document.querySelector('#zoomLevel');
const fitScreenBtn = document.querySelector('#fitScreenBtn');
const zoom100Btn = document.querySelector('#zoom100Btn');
const zoom200Btn = document.querySelector('#zoom200Btn');
const fullscreenBtn = document.querySelector('#fullscreenBtn');

const metaOriginal = document.querySelector('#metaOriginal');
const metaEnhanced = document.querySelector('#metaEnhanced');
const metaScale = document.querySelector('#metaScale');
const metaDuration = document.querySelector('#metaDuration');
const metaDevice = document.querySelector('#metaDevice');
const metaEngine = document.querySelector('#metaEngine');

// Engine Preference Elements
const enginePills = document.querySelectorAll('.engine-pill');
const engineStatusNote = document.querySelector('#engineStatusNote');
const engineBtnAuto = document.querySelector('#engineBtnAuto');
const engineBtnWebgpu = document.querySelector('#engineBtnWebgpu');
const engineBtnServer = document.querySelector('#engineBtnServer');
const engineWebgpuText = document.querySelector('#engineWebgpuText');
const engineAutoText = document.querySelector('#engineAutoText');

// State
let selectedFile = null;
let originalObjectUrl = null;
let currentPreviewUrl = null;
let currentDownloadUrl = null;
let currentDownloadName = '';
let selectedScale = 4;
let selectedEngine = 'auto'; // 'auto' | 'webgpu' | 'server'
let webgpuSupportStatus = { supported: false, reason: 'Probing WebGPU capability...' };
let originalWidth = 0;
let originalHeight = 0;
let activeDeviceName = 'MPS';

// Request & Timer Management
let enhanceAbortController = null;
let elapsedTimerInterval = null;
let enhanceStartTime = 0;

// Zoom & Pan State
let zoomLevel = 1.0;
let panX = 0;
let panY = 0;
let isPanning = false;
let panStartX = 0;
let panStartY = 0;
let isDraggingReveal = false;

// Check backend health and hardware accelerator
async function checkHealth() {
  try {
    const res = await fetch('/api/health');
    if (!res.ok) return;
    const data = await res.json();
    if (data.device) {
      activeDeviceName = data.device.toUpperCase();
      if (deviceText) {
        deviceText.textContent = `Real-ESRGAN x4plus · ${activeDeviceName}`;
      }
      if (mobileDeviceText) {
        mobileDeviceText.textContent = `Real-ESRGAN x4plus · ${activeDeviceName}`;
      }
      if (procDeviceText) {
        procDeviceText.textContent = `Real-ESRGAN · ${activeDeviceName}`;
      }
    }
  } catch (err) {
    console.debug('Health check failed:', err);
  }
}
checkHealth();

// Probe WebGPU capability on startup
async function initWebGPUProbe() {
  if (typeof window.ClearPixWebGPU !== 'undefined') {
    try {
      webgpuSupportStatus = await window.ClearPixWebGPU.checkSupport();
      console.info('[WebGPU Probe]', webgpuSupportStatus);

      if (webgpuSupportStatus.supported) {
        const gpuName = webgpuSupportStatus.adapterName || 'GPU Hardware';
        if (engineStatusNote) {
          engineStatusNote.textContent = `Hardware WebGPU ready (${gpuName})`;
        }
        if (engineAutoText) {
          engineAutoText.textContent = `On-device WebGPU active (${gpuName}). Fallback to Server AI if needed.`;
        }
        if (engineWebgpuText) {
          engineWebgpuText.textContent = `Real-ESRGAN Compact on client GPU (${gpuName}). Zero image upload.`;
        }
        if (engineBtnWebgpu) {
          engineBtnWebgpu.disabled = false;
          engineBtnWebgpu.title = 'Accelerate on local GPU';
        }
      } else {
        if (engineStatusNote) {
          engineStatusNote.textContent = `WebGPU not supported in this browser (${webgpuSupportStatus.reason})`;
        }
        if (engineAutoText) {
          engineAutoText.textContent = `Server AI (Real-ESRGAN x4plus) active. Browser does not support WebGPU.`;
        }
        if (engineWebgpuText) {
          engineWebgpuText.textContent = `Unavailable: ${webgpuSupportStatus.reason}`;
        }
        if (engineBtnWebgpu) {
          engineBtnWebgpu.disabled = true;
          engineBtnWebgpu.title = `WebGPU unavailable: ${webgpuSupportStatus.reason}`;
        }
        if (selectedEngine === 'webgpu') {
          setEnginePreference('auto');
        }
      }
    } catch (e) {
      console.warn('WebGPU probe error:', e);
      webgpuSupportStatus = { supported: false, reason: e.message || 'Probe error' };
    }
  } else {
    if (engineStatusNote) {
      engineStatusNote.textContent = 'Server AI inference engine active';
    }
  }
}

// Engine Preference Switching
function setEnginePreference(engine) {
  selectedEngine = engine;
  enginePills.forEach(pill => {
    const isMatch = pill.getAttribute('data-engine') === engine;
    pill.classList.toggle('active', isMatch);
    pill.setAttribute('aria-checked', isMatch ? 'true' : 'false');
  });
}

if (enginePills && enginePills.length > 0) {
  enginePills.forEach(pill => {
    pill.addEventListener('click', () => {
      if (pill.disabled) return;
      const engine = pill.getAttribute('data-engine');
      setEnginePreference(engine);
    });
  });
}

// Initialize WebGPU detection
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initWebGPUProbe);
} else {
  initWebGPUProbe();
}

// Error Banner Utilities
function showError(msg) {
  if (errorBanner && errorMessage) {
    errorMessage.textContent = msg || 'An error occurred during enhancement.';
    errorBanner.classList.remove('hidden');
  } else {
    alert(msg);
  }
}

function hideError() {
  if (errorBanner) {
    errorBanner.classList.add('hidden');
  }
}

// Scale Selector Handlers
scalePills.forEach(pill => {
  pill.addEventListener('click', () => {
    if (enhanceBtn && enhanceBtn.disabled) return;
    scalePills.forEach(p => {
      p.classList.remove('active');
      p.setAttribute('aria-checked', 'false');
    });
    pill.classList.add('active');
    pill.setAttribute('aria-checked', 'true');
    selectedScale = parseInt(pill.dataset.scale, 10) || 4;
    updateEstimatedOutput();
  });
});

function updateEstimatedOutput() {
  if (originalWidth && originalHeight && configOutputMeta) {
    const estW = originalWidth * selectedScale;
    const estH = originalHeight * selectedScale;
    configOutputMeta.textContent = `${estW} × ${estH} px (${selectedScale}×)`;
  }
}

function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function cleanupUrls() {
  if (originalObjectUrl) {
    URL.revokeObjectURL(originalObjectUrl);
    originalObjectUrl = null;
  }
  if (currentPreviewUrl && currentPreviewUrl.startsWith('blob:')) {
    URL.revokeObjectURL(currentPreviewUrl);
  }
  if (currentDownloadUrl && currentDownloadUrl.startsWith('blob:') && currentDownloadUrl !== currentPreviewUrl) {
    URL.revokeObjectURL(currentDownloadUrl);
  }
}

// Upload & Drag-and-Drop
if (browseBtn) {
  browseBtn.addEventListener('click', e => {
    e.stopPropagation();
    input.click();
  });
}

if (dropzone) {
  dropzone.addEventListener('click', () => input.click());
  dropzone.addEventListener('keydown', e => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      input.click();
    }
  });

  for (const type of ['dragenter', 'dragover']) {
    dropzone.addEventListener(type, e => {
      e.preventDefault();
      dropzone.classList.add('dragging');
      dropzone.classList.add('dragover');
    });
  }

  for (const type of ['dragleave', 'drop']) {
    dropzone.addEventListener(type, e => {
      e.preventDefault();
      dropzone.classList.remove('dragging');
      dropzone.classList.remove('dragover');
    });
  }

  dropzone.addEventListener('drop', e => {
    const file = e.dataTransfer && e.dataTransfer.files ? e.dataTransfer.files[0] : null;
    if (file) handleFileSelected(file);
  });
}

if (input) {
  input.addEventListener('change', () => {
    if (input.files && input.files[0]) {
      handleFileSelected(input.files[0]);
    }
  });
}

if (cancelSelectBtn) {
  cancelSelectBtn.addEventListener('click', resetToDropzone);
}

if (resetBtn) {
  resetBtn.addEventListener('click', resetToDropzone);
}

async function handleFileSelected(file) {
  if (!file) return;

  const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
  if (!validTypes.includes(file.type)) {
    showError('Please choose a JPG, PNG, or WebP image file.');
    return;
  }

  if (file.size > 25 * 1024 * 1024) {
    showError('Please choose an image smaller than 25 MB.');
    return;
  }

  hideError();
  cleanupUrls();
  selectedFile = file;
  originalObjectUrl = URL.createObjectURL(file);

  // Read dimensions via temporary Image object
  const tempImg = new Image();
  tempImg.onload = () => {
    originalWidth = tempImg.naturalWidth;
    originalHeight = tempImg.naturalHeight;

    if (configFileName) configFileName.textContent = file.name;
    if (configThumbnail) configThumbnail.src = originalObjectUrl;
    if (procHologramImg) procHologramImg.src = originalObjectUrl;
    if (configFileMeta) {
      configFileMeta.textContent = `${originalWidth} × ${originalHeight} px · ${formatBytes(file.size)}`;
    }
    updateEstimatedOutput();

    // Transition to Config View
    dropzone.classList.add('hidden');
    if (processingScreen) processingScreen.classList.add('hidden');
    editor.classList.add('hidden');
    configCard.classList.remove('hidden');
    hideError();
    setEnhancingState(false);
  };
  tempImg.onerror = () => {
    showError('Could not decode this image file. Please choose another image.');
  };
  tempImg.src = originalObjectUrl;
}

// 5 Honest Processing Stages
const HONEST_STAGES = [
  {
    title: 'Preparing your image',
    desc: 'Validating format and allocating neural tensor memory...',
    inline: '1. Validation',
  },
  {
    title: 'Loading AI model',
    desc: () => `Dispatching Real-ESRGAN x4plus weights to ${activeDeviceName}...`,
    inline: '2. Model Dispatch',
  },
  {
    title: 'Running Real-ESRGAN inference',
    desc: () => `Deep RRDBNet convolutional super-resolution active on ${activeDeviceName}...`,
    inline: '3. Super-Resolution',
  },
  {
    title: 'Reconstructing image details',
    desc: 'Synthesizing authentic micro-textures and assembling tiled boundaries...',
    inline: '4. Tile Assembly',
  },
  {
    title: 'Preparing your enhanced image',
    desc: 'Recomposing color channels and encoding lossless PNG...',
    inline: '5. PNG Encoding',
  },
];

// Honest Status Stages Updater
function updateHonestStages(elapsedSecs) {
  let currentStageIndex = 0;
  if (elapsedSecs < 0.8) currentStageIndex = 0;
  else if (elapsedSecs < 2.5) currentStageIndex = 1;
  else if (elapsedSecs < 16.0) currentStageIndex = 2;
  else if (elapsedSecs < 35.0) currentStageIndex = 3;
  else currentStageIndex = 4;

  const currentStage = HONEST_STAGES[currentStageIndex];

  // Update 3D Loading Screen Elements
  if (procStatusTitle) {
    procStatusTitle.textContent = currentStage.title;
  }
  if (procStatusDesc) {
    const descText = typeof currentStage.desc === 'function' ? currentStage.desc() : currentStage.desc;
    procStatusDesc.textContent = descText;
  }

  // Update 3D Stage Pills
  procSteps.forEach((stepEl, idx) => {
    if (!stepEl) return;
    if (idx < currentStageIndex) {
      stepEl.className = 'proc-step done';
    } else if (idx === currentStageIndex) {
      stepEl.className = 'proc-step active';
    } else {
      stepEl.className = 'proc-step';
    }
  });

  // Update Compact Backup Stage Elements
  const inlineStageIds = ['#stage1', '#stage2', '#stage3', '#stage4', '#stage5'];
  inlineStageIds.forEach((id, idx) => {
    const el = document.querySelector(id);
    if (!el) return;
    if (idx < currentStageIndex) {
      el.className = 'stage-step done';
    } else if (idx === currentStageIndex) {
      el.className = 'stage-step active';
    } else {
      el.className = 'stage-step';
    }
  });

  if (progressStatus) {
    progressStatus.textContent = currentStage.title;
  }
}

// Enhancing UI State & Timer
function setEnhancingState(isEnhancing) {
  if (enhanceBtn) enhanceBtn.disabled = isEnhancing;
  if (cancelSelectBtn) cancelSelectBtn.disabled = isEnhancing;
  scalePills.forEach(p => p.disabled = isEnhancing);

  if (isEnhancing) {
    if (btnSpinner) btnSpinner.classList.remove('hidden');
    if (btnText) btnText.textContent = 'Enhancing with AI...';
    if (progressWrap) progressWrap.classList.remove('hidden');
    if (cancelEnhanceBtn) cancelEnhanceBtn.classList.remove('hidden');

    // Switch to Dedicated 3D Processing Screen
    if (configCard) configCard.classList.add('hidden');
    if (editor) editor.classList.add('hidden');
    if (processingScreen) {
      processingScreen.classList.remove('hidden');
      if (procHologramImg && originalObjectUrl) {
        procHologramImg.src = originalObjectUrl;
      }
      if (procScaleText) {
        procScaleText.textContent = `${selectedScale}× Super-Resolution`;
      }
      if (procDeviceText) {
        procDeviceText.textContent = `Real-ESRGAN · ${activeDeviceName}`;
      }
    }

    enhanceStartTime = Date.now();
    if (elapsedTimer) elapsedTimer.textContent = '0s';
    if (procTimerVal) procTimerVal.textContent = '0.0s';
    updateHonestStages(0);

    // Start high-precision elapsed timer ticker (100ms interval)
    if (elapsedTimerInterval) clearInterval(elapsedTimerInterval);
    elapsedTimerInterval = setInterval(() => {
      const elapsedSecs = (Date.now() - enhanceStartTime) / 1000;
      if (procTimerVal) procTimerVal.textContent = `${elapsedSecs.toFixed(1)}s`;
      if (elapsedTimer) elapsedTimer.textContent = `${Math.floor(elapsedSecs)}s`;
      updateHonestStages(elapsedSecs);
    }, 100);

  } else {
    // Clear timer
    if (elapsedTimerInterval) {
      clearInterval(elapsedTimerInterval);
      elapsedTimerInterval = null;
    }
    if (btnSpinner) btnSpinner.classList.add('hidden');
    if (btnText) btnText.textContent = 'Enhance image';
    if (progressWrap) progressWrap.classList.add('hidden');
    if (cancelEnhanceBtn) cancelEnhanceBtn.classList.add('hidden');
    if (processingScreen) processingScreen.classList.add('hidden');
  }
}

// Cancel Enhancing Handlers
function handleCancelEnhance() {
  if (enhanceAbortController) {
    enhanceAbortController.abort();
    enhanceAbortController = null;
  }
  setEnhancingState(false);
  if (configCard) configCard.classList.remove('hidden');
  showError('Enhancement was cancelled by user.');
}

if (cancelEnhanceBtn) {
  cancelEnhanceBtn.addEventListener('click', handleCancelEnhance);
}

if (procCancelBtn) {
  procCancelBtn.addEventListener('click', handleCancelEnhance);
}

// Helper to generate filename for client-side download
function generateClientDownloadName(fileName, scale) {
  const lastDot = (fileName || 'photo').lastIndexOf('.');
  const base = lastDot > 0 ? fileName.slice(0, lastDot) : (fileName || 'photo');
  return `${base}_enhanced_${scale}x.png`;
}

// Server Enhancement Execution
async function executeServerEnhance(signal) {
  const formData = new FormData();
  formData.append('image', selectedFile);
  formData.append('scale', selectedScale);

  const response = await fetch('/api/enhance', {
    method: 'POST',
    body: formData,
    signal: signal,
  });

  let data;
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    data = await response.json();
  } else {
    const text = await response.text();
    throw new Error(`Server returned unexpected HTTP ${response.status}: ${text.slice(0, 100)}`);
  }

  if (!response.ok || data.status !== 'success') {
    throw new Error(data.message || `Enhancement failed (HTTP ${response.status}).`);
  }

  // Ensure engine metadata is explicitly set to Server AI
  data.engine = 'Server AI (Remote Real-ESRGAN x4plus)';
  data.isLocalWebGPU = false;
  return data;
}

// Client-Side WebGPU Enhancement Execution
async function executeWebGPUEnhance(signal) {
  if (!window.ClearPixWebGPU) {
    throw new Error('WebGPU super-resolution module is not loaded.');
  }

  // WebGPU progress callback updates UI status & stages
  const onProgress = (pct, stageName) => {
    if (progressStatus) progressStatus.textContent = stageName;
    if (procStatusDesc) procStatusDesc.textContent = stageName;
    if (progressBar) progressBar.style.width = `${Math.round(pct * 100)}%`;

    // Map percentage to honest visual stage indicators
    let stageIdx = 0;
    if (pct >= 0.95) stageIdx = 4;
    else if (pct >= 0.70) stageIdx = 3;
    else if (pct >= 0.20) stageIdx = 2;
    else if (pct >= 0.10) stageIdx = 1;

    procSteps.forEach((stepEl, idx) => {
      if (!stepEl) return;
      if (idx < stageIdx) stepEl.className = 'proc-step done';
      else if (idx === stageIdx) stepEl.className = 'proc-step active';
      else stepEl.className = 'proc-step';
    });
  };

  if (procDeviceText) {
    const gpuName = (webgpuSupportStatus && webgpuSupportStatus.adapterName) || 'Browser WebGPU';
    procDeviceText.textContent = `WebGPU · ${gpuName}`;
  }

  const res = await window.ClearPixWebGPU.enhance(
    selectedFile,
    selectedScale,
    onProgress,
    signal
  );

  const blobUrl = URL.createObjectURL(res.blob);
  const downloadName = generateClientDownloadName(selectedFile.name, selectedScale);

  return {
    status: 'success',
    preview_url: blobUrl,
    download_url: blobUrl,
    download_name: downloadName,
    output_filename: downloadName,
    original_filename: selectedFile.name,
    scale: selectedScale,
    duration_seconds: parseFloat(res.durationSeconds.toFixed(2)),
    device: res.deviceName || 'WebGPU Accelerator',
    engine: 'Browser GPU (100% On-Device WebGPU)',
    isLocalWebGPU: true,
    original_dimensions: { width: originalWidth, height: originalHeight },
    output_dimensions: { width: res.width, height: res.height },
  };
}

// Enhance Submission
if (enhanceBtn) {
  enhanceBtn.addEventListener('click', async () => {
    if (!selectedFile || enhanceBtn.disabled) return;

    hideError();
    setEnhancingState(true);

    enhanceAbortController = new AbortController();
    const signal = enhanceAbortController.signal;

    try {
      let data = null;

      if (selectedEngine === 'webgpu') {
        // Strict WebGPU requirement: do NOT send to server
        if (!webgpuSupportStatus.supported) {
          throw new Error(`WebGPU is unavailable: ${webgpuSupportStatus.reason}. Please select Server AI or Automatic.`);
        }
        data = await executeWebGPUEnhance(signal);

      } else if (selectedEngine === 'auto') {
        // Automatic preference: try local WebGPU first if supported, fallback to Server AI on failure
        if (webgpuSupportStatus.supported && typeof window.ClearPixWebGPU !== 'undefined') {
          try {
            console.info('[Auto Engine] Attempting local WebGPU super-resolution...');
            data = await executeWebGPUEnhance(signal);
          } catch (gpuErr) {
            if (gpuErr.name === 'AbortError') throw gpuErr; // User cancelled
            console.warn('[Auto Engine] WebGPU execution failed; seamlessly falling back to Server AI:', gpuErr);
            if (procDeviceText) {
              procDeviceText.textContent = `Server AI · ${activeDeviceName} (Fallback)`;
            }
            if (progressStatus) {
              progressStatus.textContent = 'Switching seamlessly to Server AI...';
            }
            data = await executeServerEnhance(signal);
          }
        } else {
          // WebGPU not available on device, route cleanly to Server AI
          console.info('[Auto Engine] WebGPU not supported on this device/browser. Routing to Server AI.');
          data = await executeServerEnhance(signal);
        }

      } else {
        // Server AI explicitly selected by user
        data = await executeServerEnhance(signal);
      }

      // Success: populate comparison viewer with smooth transition
      displayComparisonResult(data);

    } catch (err) {
      if (err.name === 'AbortError') {
        console.info('Enhancement request was aborted.');
        showError('Enhancement was cancelled.');
      } else {
        console.error('Enhance request error:', err);
        showError(err.message || 'An error occurred during enhancement.');
      }
      setEnhancingState(false);
      if (configCard) configCard.classList.remove('hidden');
    } finally {
      enhanceAbortController = null;
    }
  });
}

// Display AI Output in Comparison Viewer
function displayComparisonResult(data) {
  hideError();
  setEnhancingState(false);
  if (configCard) configCard.classList.add('hidden');
  if (processingScreen) processingScreen.classList.add('hidden');
  editor.classList.remove('hidden');

  currentPreviewUrl = data.preview_url;
  currentDownloadUrl = data.download_url;
  currentDownloadName = data.download_name || data.output_filename || `clearpix_enhanced_${data.scale}x.png`;

  const origW = data.original_dimensions.width;
  const origH = data.original_dimensions.height;
  const outW = data.output_dimensions.width;
  const outH = data.output_dimensions.height;

  if (fileNameEl) fileNameEl.textContent = data.original_filename;
  if (dimensionsEl) dimensionsEl.textContent = `Original: ${origW} × ${origH} px`;

  const isWebGPU = Boolean(data.isLocalWebGPU);

  if (afterBadge) {
    afterBadge.textContent = isWebGPU ? `WEBGPU AI ${data.scale}×` : `AI ENHANCED ${data.scale}×`;
  }

  if (outputDimensionsEl) {
    if (isWebGPU) {
      outputDimensionsEl.textContent = `WebGPU AI (${outW} × ${outH} px) · ${data.duration_seconds}s on ${data.device}`;
    } else {
      outputDimensionsEl.textContent = `Real-ESRGAN AI (${outW} × ${outH} px) · ${data.duration_seconds}s on ${(data.device || 'CPU').toUpperCase()}`;
    }
  }

  // Populate comprehensive output metadata grid
  if (metaOriginal) metaOriginal.textContent = `${origW} × ${origH} px`;
  if (metaEnhanced) metaEnhanced.textContent = `${outW} × ${outH} px`;
  if (metaScale) metaScale.textContent = isWebGPU ? `${data.scale}× Real-ESRGAN Compact` : `${data.scale}× Real-ESRGAN x4plus`;
  if (metaDuration) metaDuration.textContent = `${data.duration_seconds}s`;

  if (metaDevice) {
    if (isWebGPU) {
      metaDevice.textContent = data.device;
    } else {
      const devUpper = (data.device || 'CPU').toUpperCase();
      const devLabel = devUpper === 'MPS' ? 'Server GPU (Apple Silicon MPS)' :
                       devUpper === 'CUDA' ? 'Server GPU (NVIDIA CUDA)' :
                       `Server ${devUpper}`;
      metaDevice.textContent = devLabel;
    }
  }

  if (metaEngine) {
    if (isWebGPU) {
      metaEngine.textContent = 'Browser GPU (100% On-Device)';
      metaEngine.className = 'meta-val highlight-val';
    } else {
      metaEngine.textContent = 'Server AI (Remote Host)';
      metaEngine.className = 'meta-val';
    }
  }

  // Set original preview image
  original.src = originalObjectUrl;
  // Set enhanced preview image
  enlarged.src = currentPreviewUrl;

  enlarged.onload = () => {
    updateNativeScale();
    setZoom(1.0, true);
  };

  // Reset zoom & pan to default fit
  setZoom(1.0, true);

  // Initialize comparison divider at 50%
  setReveal(50);
  if (status) {
    if (isWebGPU) {
      status.textContent = `Enhanced ${origW}×${origH} to ${outW}×${outH} px locally in browser on ${data.device} in ${data.duration_seconds}s (Zero data uploaded).`;
    } else {
      status.textContent = `Enhanced ${origW}×${origH} to ${outW}×${outH} px using Real-ESRGAN x4plus in ${data.duration_seconds}s on ${(data.device || 'CPU').toUpperCase()}.`;
    }
  }
}

// Download Button
if (downloadBtn) {
  downloadBtn.addEventListener('click', () => {
    if (!currentDownloadUrl) return;
    const a = document.createElement('a');
    a.href = currentDownloadUrl;
    if (currentDownloadName) {
      a.download = currentDownloadName;
    }
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  });
}

function resetToDropzone() {
  if (enhanceAbortController) {
    enhanceAbortController.abort();
    enhanceAbortController = null;
  }
  hideError();
  cleanupUrls();
  selectedFile = null;
  currentPreviewUrl = null;
  currentDownloadUrl = null;
  currentDownloadName = '';
  originalWidth = 0;
  originalHeight = 0;

  if (input) input.value = '';
  if (configThumbnail) configThumbnail.removeAttribute('src');
  if (procHologramImg) procHologramImg.removeAttribute('src');
  if (configCard) configCard.classList.add('hidden');
  if (processingScreen) processingScreen.classList.add('hidden');
  if (editor) editor.classList.add('hidden');
  if (dropzone) dropzone.classList.remove('hidden');
  if (original) original.removeAttribute('src');
  if (enlarged) enlarged.removeAttribute('src');
  if (status) status.textContent = '';
  setEnhancingState(false);
  setZoom(1.0, true);
  setReveal(50);
}

// ==========================================
// ==========================================
// Zoom & Fit Controls
// ==========================================
let currentNativeScale = 1.0;

function updateNativeScale() {
  if (enlarged && enlarged.naturalWidth && enlarged.clientWidth) {
    currentNativeScale = Math.max(1.0, enlarged.naturalWidth / enlarged.clientWidth);
  } else {
    currentNativeScale = 1.0;
  }
}

function setZoom(newZoom, resetPan = false) {
  updateNativeScale();
  const maxZoom = Math.max(4.0, Math.ceil(currentNativeScale * 2.5));
  zoomLevel = Math.max(1.0, Math.min(maxZoom, Math.round(newZoom * 100) / 100));

  if (zoomLevel === 1.0 || resetPan) {
    panX = 0;
    panY = 0;
  }

  // Determine active display mode
  const isFit = Math.abs(zoomLevel - 1.0) < 0.02;
  const is100 = Math.abs(zoomLevel - currentNativeScale) < 0.08 || (currentNativeScale <= 1.05 && isFit);
  const is200 = Math.abs(zoomLevel - (currentNativeScale * 2.0)) < 0.15;

  if (zoomLevelEl) {
    if (isFit && currentNativeScale > 1.1) {
      zoomLevelEl.textContent = 'Fit';
    } else if (is100) {
      zoomLevelEl.textContent = '100%';
    } else if (is200) {
      zoomLevelEl.textContent = '200%';
    } else {
      const pct = Math.round((zoomLevel / currentNativeScale) * 100);
      zoomLevelEl.textContent = `${pct}%`;
    }
  }

  [fitScreenBtn, zoom100Btn, zoom200Btn].forEach(b => {
    if (b) b.classList.remove('active');
  });

  if (isFit && fitScreenBtn && (!is100 || currentNativeScale > 1.1)) fitScreenBtn.classList.add('active');
  if (is100 && zoom100Btn) zoom100Btn.classList.add('active');
  if (is200 && zoom200Btn) zoom200Btn.classList.add('active');

  applyTransform();
}

function applyTransform() {
  if (!previewWrap) return;

  if (zoomLevel > 1.0) {
    const stageRect = previewStage.getBoundingClientRect();
    const wrapW = previewWrap.offsetWidth * zoomLevel;
    const wrapH = previewWrap.offsetHeight * zoomLevel;
    const maxPanX = Math.max(0, (wrapW - stageRect.width) / 2 + 20);
    const maxPanY = Math.max(0, (wrapH - stageRect.height) / 2 + 20);
    panX = Math.max(-maxPanX, Math.min(maxPanX, panX));
    panY = Math.max(-maxPanY, Math.min(maxPanY, panY));
  } else {
    panX = 0;
    panY = 0;
  }

  previewWrap.style.transform = `scale(${zoomLevel}) translate(${panX / zoomLevel}px, ${panY / zoomLevel}px)`;
  if (previewStage) {
    previewStage.style.cursor = zoomLevel > 1.0 ? 'grab' : 'default';
  }
}

// Zoom toolbar button events
if (zoomInBtn) {
  zoomInBtn.addEventListener('click', () => {
    updateNativeScale();
    const step = Math.max(0.25, currentNativeScale * 0.25);
    setZoom(zoomLevel + step);
  });
}
if (zoomOutBtn) {
  zoomOutBtn.addEventListener('click', () => {
    updateNativeScale();
    const step = Math.max(0.25, currentNativeScale * 0.25);
    setZoom(zoomLevel - step);
  });
}
if (fitScreenBtn) fitScreenBtn.addEventListener('click', () => setZoom(1.0, true));
if (zoom100Btn) {
  zoom100Btn.addEventListener('click', () => {
    updateNativeScale();
    setZoom(currentNativeScale, true);
  });
}
if (zoom200Btn) {
  zoom200Btn.addEventListener('click', () => {
    updateNativeScale();
    setZoom(currentNativeScale * 2.0, true);
  });
}

// Mouse-wheel zoom on preview stage
if (previewStage) {
  previewStage.addEventListener('wheel', e => {
    e.preventDefault();
    updateNativeScale();
    const step = Math.max(0.15, currentNativeScale * 0.15);
    const delta = e.deltaY < 0 ? step : -step;
    setZoom(zoomLevel + delta);
  }, { passive: false });

  // Pan interaction on click + drag
  previewStage.addEventListener('mousedown', e => {
    if (e.target === slider || e.target.closest('.zoom-toolbar')) return;

    if (zoomLevel > 1.0) {
      const stageRect = previewStage.getBoundingClientRect();
      const clickX = e.clientX - stageRect.left;
      const sliderPct = Number(slider ? slider.value : 50);
      const dividerPixelX = (stageRect.width * sliderPct) / 100;

      if (Math.abs(clickX - dividerPixelX) > 28) {
        isPanning = true;
        panStartX = e.clientX - panX;
        panStartY = e.clientY - panY;
        previewStage.style.cursor = 'grabbing';
      }
    }
  });

  window.addEventListener('mousemove', e => {
    if (!isPanning) return;
    panX = e.clientX - panStartX;
    panY = e.clientY - panStartY;
    applyTransform();
  });

  window.addEventListener('mouseup', () => {
    if (isPanning) {
      isPanning = false;
      if (previewStage) {
        previewStage.style.cursor = zoomLevel > 1.0 ? 'grab' : 'default';
      }
    }
  });
}

// Comparison Split Reveal Slider
function setReveal(pct) {
  const clamped = Math.max(0, Math.min(100, pct));
  if (slider) slider.value = clamped;
  if (beforePane) {
    beforePane.style.clipPath = `polygon(0 0, ${clamped}% 0, ${clamped}% 100%, 0 100%)`;
  }
  if (sliderLine) {
    sliderLine.style.left = `${clamped}%`;
  }
}

if (slider) {
  slider.addEventListener('input', e => {
    setReveal(Number(e.target.value));
  });
}

// Retry Button on Error Banner
if (retryBtn) {
  retryBtn.addEventListener('click', () => {
    hideError();
    if (enhanceBtn) enhanceBtn.click();
  });
}

// Fullscreen Comparison Mode
if (fullscreenBtn && previewStage) {
  fullscreenBtn.addEventListener('click', () => {
    if (!document.fullscreenElement) {
      previewStage.requestFullscreen().catch(err => {
        console.debug('Fullscreen request failed:', err);
      });
    } else {
      document.exitFullscreen().catch(err => {
        console.debug('Exit fullscreen failed:', err);
      });
    }
  });

  document.addEventListener('fullscreenchange', () => {
    if (document.fullscreenElement) {
      fullscreenBtn.textContent = '✕';
      fullscreenBtn.title = 'Exit Fullscreen (Esc)';
      fullscreenBtn.classList.add('active');
    } else {
      fullscreenBtn.textContent = '⛶';
      fullscreenBtn.title = 'Toggle Fullscreen (F)';
      fullscreenBtn.classList.remove('active');
    }
  });
}

// Keyboard Shortcuts in Workspace
window.addEventListener('keydown', e => {
  if (!editor || editor.classList.contains('hidden')) return;
  if (e.target.tagName === 'INPUT' && e.target.type !== 'range') return;

  if (e.key === 'ArrowLeft') {
    e.preventDefault();
    const current = Number(slider ? slider.value : 50);
    setReveal(Math.max(0, current - 5));
  } else if (e.key === 'ArrowRight') {
    e.preventDefault();
    const current = Number(slider ? slider.value : 50);
    setReveal(Math.min(100, current + 5));
  } else if (e.key === 'f' || e.key === 'F') {
    if (fullscreenBtn) fullscreenBtn.click();
  } else if (e.key === '+' || e.key === '=') {
    setZoom(zoomLevel + 0.25);
  } else if (e.key === '-' || e.key === '_') {
    setZoom(zoomLevel - 0.25);
  } else if (e.key === '0') {
    setZoom(1.0, true);
  }
});

// ==========================================================================
// Interactive 3D Perspective Tilt for Upload Panel & Feature Cards
// ==========================================================================
function init3DTilt() {
  const isTouchDevice = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0) || window.matchMedia('(hover: none) or (pointer: coarse)').matches;
  const supportsFinePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (isTouchDevice || !supportsFinePointer || prefersReducedMotion) return;

  // 1. Upload Panel Tilt & Mouse Glow
  if (dropzone) {
    let dropzoneRaf = null;

    dropzone.addEventListener('mousemove', e => {
      if (dropzone.classList.contains('dragging')) return;

      const rect = dropzone.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      const normX = (x / rect.width) - 0.5;
      const normY = (y / rect.height) - 0.5;

      const rotX = -normY * 8; // Max 4 deg tilt
      const rotY = normX * 8;

      if (dropzoneRaf) cancelAnimationFrame(dropzoneRaf);
      dropzoneRaf = requestAnimationFrame(() => {
        dropzone.style.setProperty('--mouse-x', `${(x / rect.width) * 100}%`);
        dropzone.style.setProperty('--mouse-y', `${(y / rect.height) * 100}%`);
        dropzone.style.transform = `perspective(1000px) rotateX(${rotX.toFixed(2)}deg) rotateY(${rotY.toFixed(2)}deg) translateY(-2px)`;
      });
    });

    dropzone.addEventListener('mouseleave', () => {
      if (dropzoneRaf) cancelAnimationFrame(dropzoneRaf);
      dropzone.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) translateY(0)';
    });
  }

  // 2. Feature Cards 3D Tilt
  const benefitCards = document.querySelectorAll('.benefit-card, .benefits article');
  benefitCards.forEach(card => {
    let cardRaf = null;

    card.addEventListener('mousemove', e => {
      const rect = card.getBoundingClientRect();
      const normX = ((e.clientX - rect.left) / rect.width) - 0.5;
      const normY = ((e.clientY - rect.top) / rect.height) - 0.5;

      const rotX = -normY * 7;
      const rotY = normX * 7;

      if (cardRaf) cancelAnimationFrame(cardRaf);
      cardRaf = requestAnimationFrame(() => {
        card.style.transform = `perspective(800px) rotateX(${rotX.toFixed(2)}deg) rotateY(${rotY.toFixed(2)}deg) translateY(-4px)`;
      });
    });

    card.addEventListener('mouseleave', () => {
      if (cardRaf) cancelAnimationFrame(cardRaf);
      card.style.transform = 'perspective(800px) rotateX(0deg) rotateY(0deg) translateY(0)';
    });
  });
}

// Initialize Interactive 3D on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init3DTilt);
} else {
  init3DTilt();
}

// ==========================================================================
// Mobile Navigation Drawer Controller
// ==========================================================================
function isMobileDrawerOpen() {
  return mobileDrawer && mobileDrawer.classList.contains('is-open');
}

function openMobileDrawer() {
  if (!mobileDrawer) return;
  mobileDrawer.classList.add('is-open');
  mobileDrawer.setAttribute('aria-hidden', 'false');
  if (mobileMenuBtn) {
    mobileMenuBtn.setAttribute('aria-expanded', 'true');
    mobileMenuBtn.classList.add('is-active');
  }
  if (mobileDrawerBackdrop) {
    mobileDrawerBackdrop.classList.add('is-open');
    mobileDrawerBackdrop.setAttribute('aria-hidden', 'false');
  }
  document.body.classList.add('menu-open');
}

function closeMobileDrawer() {
  if (!mobileDrawer) return;
  mobileDrawer.classList.remove('is-open');
  mobileDrawer.setAttribute('aria-hidden', 'true');
  if (mobileMenuBtn) {
    mobileMenuBtn.setAttribute('aria-expanded', 'false');
    mobileMenuBtn.classList.remove('is-active');
  }
  if (mobileDrawerBackdrop) {
    mobileDrawerBackdrop.classList.remove('is-open');
    mobileDrawerBackdrop.setAttribute('aria-hidden', 'true');
  }
  document.body.classList.remove('menu-open');
}

function toggleMobileDrawer() {
  if (isMobileDrawerOpen()) {
    closeMobileDrawer();
  } else {
    openMobileDrawer();
  }
}

if (mobileMenuBtn) {
  mobileMenuBtn.addEventListener('click', e => {
    e.stopPropagation();
    toggleMobileDrawer();
  });
}

if (mobileDrawerBackdrop) {
  mobileDrawerBackdrop.addEventListener('click', () => {
    closeMobileDrawer();
  });
}

if (mobileNavItems && mobileNavItems.length > 0) {
  mobileNavItems.forEach(item => {
    item.addEventListener('click', () => {
      closeMobileDrawer();
    });
  });
}

// Close drawer with Escape key or viewport widening
window.addEventListener('keydown', e => {
  if (e.key === 'Escape' && isMobileDrawerOpen()) {
    closeMobileDrawer();
  }
});

window.addEventListener('resize', () => {
  if (window.innerWidth > 860 && isMobileDrawerOpen()) {
    closeMobileDrawer();
  }
});

// Comparison Touch Drag Support on Mobile / Touch Screens
if (previewStage && slider) {
  let isSliderTouching = false;

  const updateRevealFromTouch = (touch) => {
    const rect = previewStage.getBoundingClientRect();
    if (rect.width <= 0) return;
    const clientX = touch.clientX;
    const pct = Math.max(0, Math.min(100, ((clientX - rect.left) / rect.width) * 100));
    setReveal(pct);
  };

  previewStage.addEventListener('touchstart', e => {
    if (zoomLevel <= 1.05 && e.touches.length === 1) {
      isSliderTouching = true;
      updateRevealFromTouch(e.touches[0]);
    }
  }, { passive: true });

  previewStage.addEventListener('touchmove', e => {
    if (isSliderTouching && zoomLevel <= 1.05 && e.touches.length === 1) {
      updateRevealFromTouch(e.touches[0]);
    }
  }, { passive: true });

  previewStage.addEventListener('touchend', () => {
    isSliderTouching = false;
  });

  previewStage.addEventListener('touchcancel', () => {
    isSliderTouching = false;
  });
}

// Theme Toggle & Mode Management
const themeToggleBtn = document.querySelector('#themeToggleBtn');
if (themeToggleBtn) {
  themeToggleBtn.addEventListener('click', () => {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', nextTheme);
    try {
      localStorage.setItem('clearpix-theme', nextTheme);
    } catch (e) {}
    const themeMeta = document.getElementById('themeMeta');
    if (themeMeta) {
      themeMeta.setAttribute('content', nextTheme === 'dark' ? '#0f100e' : '#f9f9f7');
    }
  });
}

// Listen to OS theme changes if user hasn't explicitly overridden preference
try {
  const mql = window.matchMedia('(prefers-color-scheme: dark)');
  mql.addEventListener('change', e => {
    try {
      if (!localStorage.getItem('clearpix-theme')) {
        const nextTheme = e.matches ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', nextTheme);
        const themeMeta = document.getElementById('themeMeta');
        if (themeMeta) {
          themeMeta.setAttribute('content', nextTheme === 'dark' ? '#0f100e' : '#f9f9f7');
        }
      }
    } catch (err) {}
  });
} catch (e) {}
