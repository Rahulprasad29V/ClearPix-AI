import sys

js_content = """// ClearPix AI Photo Upscaler Client — Production Engine with 3D Effects & Loading Experience

// DOM Elements - Navigation & Dropzone
const input = document.querySelector('#fileInput');
const dropzone = document.querySelector('#dropzone');
const browseBtn = document.querySelector('#browseBtn');
const deviceText = document.querySelector('#deviceText');

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
const afterPane = document.querySelector('#afterPane');
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

// State
let selectedFile = null;
let originalObjectUrl = null;
let currentPreviewUrl = null;
let currentDownloadUrl = null;
let selectedScale = 4;
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
      if (procDeviceText) {
        procDeviceText.textContent = `Real-ESRGAN · ${activeDeviceName}`;
      }
    }
  } catch (err) {
    console.debug('Health check failed:', err);
  }
}
checkHealth();

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

// Enhance Submission
if (enhanceBtn) {
  enhanceBtn.addEventListener('click', async () => {
    if (!selectedFile || enhanceBtn.disabled) return;

    hideError();
    setEnhancingState(true);

    enhanceAbortController = new AbortController();

    const formData = new FormData();
    formData.append('image', selectedFile);
    formData.append('scale', selectedScale);

    try {
      const response = await fetch('/api/enhance', {
        method: 'POST',
        body: formData,
        signal: enhanceAbortController.signal,
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
        const errorMsg = data.message || `Enhancement failed (HTTP ${response.status}).`;
        showError(errorMsg);
        setEnhancingState(false);
        if (configCard) configCard.classList.remove('hidden');
        return;
      }

      // Success: populate comparison viewer with smooth transition
      displayComparisonResult(data);

    } catch (err) {
      if (err.name === 'AbortError') {
        console.info('Enhancement request was aborted.');
        showError('Enhancement was cancelled.');
      } else {
        console.error('Enhance request error:', err);
        showError(err.message || 'Network or server error during enhancement. Check the server console.');
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

  const origW = data.original_dimensions.width;
  const origH = data.original_dimensions.height;
  const outW = data.output_dimensions.width;
  const outH = data.output_dimensions.height;

  if (fileNameEl) fileNameEl.textContent = data.original_filename;
  if (dimensionsEl) dimensionsEl.textContent = `Original: ${origW} × ${origH} px`;
  if (afterBadge) afterBadge.textContent = `AI ENHANCED ${data.scale}×`;
  if (outputDimensionsEl) {
    outputDimensionsEl.textContent = `Real-ESRGAN AI (${outW} × ${outH} px) · ${data.duration_seconds}s on ${data.device.toUpperCase()}`;
  }

  // Populate comprehensive output metadata grid
  if (metaOriginal) metaOriginal.textContent = `${origW} × ${origH} px`;
  if (metaEnhanced) metaEnhanced.textContent = `${outW} × ${outH} px`;
  if (metaScale) metaScale.textContent = `${data.scale}× Real-ESRGAN`;
  if (metaDuration) metaDuration.textContent = `${data.duration_seconds}s`;
  if (metaDevice) metaDevice.textContent = `Apple Silicon (${data.device.toUpperCase()})`;

  // Reset zoom & pan to default fit
  setZoom(1.0, true);

  // Set original preview image
  original.src = originalObjectUrl;
  // Set enhanced preview image
  enlarged.src = currentPreviewUrl;

  // Initialize comparison divider at 50%
  setReveal(50);
  if (status) {
    status.textContent = `Enhanced ${origW}×${origH} to ${outW}×${outH} px using Real-ESRGAN x4plus in ${data.duration_seconds}s on ${data.device.toUpperCase()}.`;
  }
}

// Download Button
if (downloadBtn) {
  downloadBtn.addEventListener('click', () => {
    if (!currentDownloadUrl) return;
    const a = document.createElement('a');
    a.href = currentDownloadUrl;
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
// Zoom & Fit Controls
// ==========================================
function setZoom(newZoom, resetPan = false) {
  zoomLevel = Math.max(1.0, Math.min(4.0, Math.round(newZoom * 100) / 100));
  if (zoomLevel === 1.0 || resetPan) {
    panX = 0;
    panY = 0;
  }

  // Update zoom toolbar labels and active pills
  if (zoomLevelEl) {
    zoomLevelEl.textContent = `${Math.round(zoomLevel * 100)}%`;
  }

  [fitScreenBtn, zoom100Btn, zoom200Btn].forEach(b => {
    if (b) b.classList.remove('active');
  });

  if (zoomLevel === 1.0 && fitScreenBtn) fitScreenBtn.classList.add('active');
  if (Math.abs(zoomLevel - 1.0) < 0.02 && zoom100Btn) zoom100Btn.classList.add('active');
  if (Math.abs(zoomLevel - 2.0) < 0.02 && zoom200Btn) zoom200Btn.classList.add('active');

  applyTransform();
}

function applyTransform() {
  if (!previewWrap) return;

  if (zoomLevel > 1.0) {
    const stageRect = previewStage.getBoundingClientRect();
    const maxPanX = (stageRect.width * (zoomLevel - 1)) / 2;
    const maxPanY = (stageRect.height * (zoomLevel - 1)) / 2;
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
if (zoomInBtn) zoomInBtn.addEventListener('click', () => setZoom(zoomLevel + 0.25));
if (zoomOutBtn) zoomOutBtn.addEventListener('click', () => setZoom(zoomLevel - 0.25));
if (fitScreenBtn) fitScreenBtn.addEventListener('click', () => setZoom(1.0, true));
if (zoom100Btn) zoom100Btn.addEventListener('click', () => setZoom(1.0, true));
if (zoom200Btn) zoom200Btn.addEventListener('click', () => setZoom(2.0, true));

// Mouse-wheel zoom on preview stage
if (previewStage) {
  previewStage.addEventListener('wheel', e => {
    e.preventDefault();
    const delta = e.deltaY < 0 ? 0.15 : -0.15;
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
  if (afterPane) {
    afterPane.style.clipPath = `polygon(0 0, ${clamped}% 0, ${clamped}% 100%, 0 100%)`;
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
  const supportsFinePointer = window.matchMedia('(pointer: fine)').matches;
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (!supportsFinePointer || prefersReducedMotion) return;

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
"""

with open("static/app.js", "w") as f:
    f.write(js_content)

print(f"Successfully wrote {len(js_content)} characters to static/app.js")
