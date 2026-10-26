import sys

css_content = """/* ==========================================================================
   ClearPix — Professional AI Photo Enhancer Stylesheet
   Modern creative-tool aesthetic: warm off-white, charcoal typography,
   subtle neutral borders, refined shadows, vibrant ClearPix lime accents,
   and interactive 3D perspectives with dedicated cinematic 3D loading.
   ========================================================================== */

:root {
  /* Surface & Background */
  --bg: #f9f9f7;
  --bg-subtle: #f2f3ee;
  --surface: #ffffff;
  --surface-alt: #fbfbfa;
  --surface-hover: #f5f6f1;
  --stage-bg: #e9ece4;

  /* Typography Colors */
  --ink: #161814;
  --ink-secondary: #383a33;
  --muted: #64685e;
  --muted-light: #8e9287;

  /* Neutral Borders */
  --line: #e3e5de;
  --line-strong: #cfd2c8;
  --line-light: #ecefe8;

  /* ClearPix Signature Lime Green Brand Accent */
  --green: #bbf444;
  --green-hover: #aaf026;
  --green-active: #95df12;
  --green-dark: #203a0c;
  --green-surface: #f3fae8;
  --green-border: #7db531;
  --green-glow: rgba(187, 244, 68, 0.45);
  --green-deep-glow: rgba(187, 244, 68, 0.25);

  /* Elevation Shadows */
  --shadow-xs: 0 1px 2px rgba(22, 24, 20, 0.04);
  --shadow-sm: 0 1px 3px rgba(22, 24, 20, 0.05), 0 1px 2px rgba(22, 24, 20, 0.03);
  --shadow-md: 0 4px 16px rgba(22, 24, 20, 0.06), 0 1px 3px rgba(22, 24, 20, 0.04);
  --shadow-lg: 0 12px 36px rgba(22, 24, 20, 0.08), 0 4px 12px rgba(22, 24, 20, 0.04);
  --shadow-float: 0 14px 40px rgba(0, 0, 0, 0.12), 0 3px 8px rgba(0, 0, 0, 0.06);
  --shadow-3d: 0 20px 50px -10px rgba(22, 24, 20, 0.12), 0 8px 24px -4px rgba(22, 24, 20, 0.06);

  /* Radius Scale */
  --radius-xs: 4px;
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 18px;
  --radius-xl: 24px;
  --radius-pill: 9999px;

  /* Typography */
  --font-sans: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  --font-mono: ui-monospace, 'SF Mono', Menlo, Consolas, monospace;
}

/* ==========================================================================
   CSS Reset & Base Rules
   ========================================================================== */
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  scroll-behavior: smooth;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}

body {
  font-family: var(--font-sans);
  color: var(--ink);
  background-color: var(--bg);
  background-attachment: fixed;
  line-height: 1.5;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  overflow-x: hidden;
  position: relative;
}

/* Global Link Reset */
a,
a:visited {
  color: inherit;
  text-decoration: none;
  transition: color 0.15s ease, opacity 0.15s ease;
}

button {
  font-family: inherit;
  border: none;
  background: none;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}

/* Native file input MUST be completely hidden */
#fileInput,
input[type="file"] {
  display: none !important;
  opacity: 0 !important;
  position: absolute !important;
  width: 0.1px !important;
  height: 0.1px !important;
  overflow: hidden !important;
  pointer-events: none !important;
}

/* Focus & Accessibility */
:focus-visible {
  outline: 2px solid var(--green-border);
  outline-offset: 2px;
}

/* Responsive Content Container */
.content-container,
.main-container {
  width: 100%;
  max-width: 1080px;
  margin: 0 auto;
  padding: 0 24px;
}

main {
  flex: 1;
}

/* ==========================================================================
   0. Ambient 3D Animated Background Lighting
   ========================================================================== */
.ambient-backdrop {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}

.ambient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.65;
  will-change: transform;
}

.ambient-orb.orb-1 {
  width: 580px;
  height: 580px;
  top: -120px;
  right: -80px;
  background: radial-gradient(circle, rgba(187, 244, 68, 0.15) 0%, rgba(187, 244, 68, 0.03) 65%, transparent 75%);
  animation: float-orb-1 22s ease-in-out infinite alternate;
}

.ambient-orb.orb-2 {
  width: 680px;
  height: 680px;
  bottom: -150px;
  left: -120px;
  background: radial-gradient(circle, rgba(125, 181, 49, 0.13) 0%, rgba(200, 235, 170, 0.04) 65%, transparent 75%);
  animation: float-orb-2 26s ease-in-out infinite alternate;
}

.ambient-grid {
  position: absolute;
  inset: 0;
  background-image: 
    linear-gradient(to right, rgba(22, 24, 20, 0.02) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(22, 24, 20, 0.02) 1px, transparent 1px);
  background-size: 56px 56px;
  opacity: 0.7;
}

@keyframes float-orb-1 {
  0% { transform: translate3d(0, 0, 0) scale(1); }
  50% { transform: translate3d(-60px, 80px, 0) scale(1.08); }
  100% { transform: translate3d(40px, 120px, 0) scale(0.95); }
}

@keyframes float-orb-2 {
  0% { transform: translate3d(0, 0, 0) scale(1); }
  50% { transform: translate3d(80px, -70px, 0) scale(1.12); }
  100% { transform: translate3d(-50px, -110px, 0) scale(0.92); }
}

/* ==========================================================================
   1. Top Navigation Bar
   ========================================================================== */
.topbar {
  position: sticky;
  top: 0;
  z-index: 50;
  background: rgba(249, 249, 247, 0.92);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--line);
  transition: border-color 0.2s ease, background 0.2s ease;
}

.topbar-inner {
  max-width: 1080px;
  margin: 0 auto;
  padding: 14px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.brand-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: var(--ink);
  font-weight: 800;
  font-size: 19px;
  letter-spacing: -0.6px;
}

.brand:hover {
  opacity: 0.85;
}

.brand-mark {
  color: #55831f;
  font-size: 20px;
  line-height: 1;
  display: inline-block;
  transform: translateY(-0.5px);
}

.brand-text .dot {
  color: #659a24;
}

.brand-descriptor {
  font-size: 11px;
  font-weight: 600;
  color: var(--muted);
  background: #edece5;
  padding: 3px 8px;
  border-radius: var(--radius-sm);
  letter-spacing: 0.2px;
}

.nav-links,
.topbar nav {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-links a,
.topbar nav a,
.nav-link {
  font-size: 13.5px;
  font-weight: 550;
  color: var(--muted);
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  transition: all 0.15s ease;
}

.nav-links a:hover,
.topbar nav a:hover,
.nav-link:hover,
.nav-link.active {
  color: var(--ink);
  background: rgba(0, 0, 0, 0.04);
}

.privacy-pill {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 11px;
  font-weight: 600;
  color: var(--ink-secondary);
  background: var(--surface);
  border: 1px solid var(--line);
  padding: 5px 12px;
  border-radius: var(--radius-pill);
  box-shadow: var(--shadow-xs);
  white-space: nowrap;
  margin-left: 8px;
}

.green-dot {
  width: 7px;
  height: 7px;
  background: #55931e;
  border-radius: 50%;
  box-shadow: 0 0 0 2px rgba(85, 147, 30, 0.25);
  animation: pulse-dot 2.5s infinite ease-in-out;
  flex-shrink: 0;
}

@keyframes pulse-dot {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.2); opacity: 0.75; }
}

/* ==========================================================================
   2. Hero Section
   ========================================================================== */
.hero-section,
.intro {
  text-align: center;
  max-width: 680px;
  margin: 0 auto;
  padding: 38px 20px 22px;
  position: relative;
  z-index: 1;
}

.trust-pill,
.intro .eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  color: #385d1c;
  background: var(--green-surface);
  border: 1px solid rgba(125, 181, 49, 0.35);
  padding: 4px 12px;
  border-radius: var(--radius-pill);
  margin-bottom: 16px;
}

.sparkle {
  color: #4b7825;
}

.hero-headline,
.intro h1 {
  font-size: clamp(32px, 5vw, 46px);
  font-weight: 800;
  line-height: 1.12;
  letter-spacing: -1.2px;
  margin: 0 0 14px;
  color: var(--ink);
}

.hero-headline span,
.intro h1 span {
  color: #4c7725;
  font-weight: 800;
}

.hero-subtext,
.intro .lead {
  font-size: clamp(14px, 2vw, 16px);
  color: var(--muted);
  line-height: 1.6;
  margin: 0 auto;
  max-width: 540px;
}

/* ==========================================================================
   3. Workspace & Interactive 3D Upload Panel
   ========================================================================== */
.workspace {
  max-width: 860px;
  margin: 16px auto 44px;
  width: 100%;
  position: relative;
  z-index: 2;
  perspective: 1200px;
}

/* State 1: Dropzone Upload Box with 3D perspective and glow */
.dropzone {
  min-height: 310px;
  background: var(--surface);
  border: 2px dashed var(--line-strong);
  border-radius: var(--radius-lg);
  padding: 44px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  cursor: pointer;
  box-shadow: var(--shadow-sm);
  outline: none;
  position: relative;
  overflow: hidden;
  transform-style: preserve-3d;
  transition: transform 0.18s cubic-bezier(0.16, 1, 0.3, 1), 
              box-shadow 0.25s cubic-bezier(0.16, 1, 0.3, 1),
              border-color 0.2s ease,
              background-color 0.2s ease;
  will-change: transform;
}

/* Interactive cursor light on hover */
.dropzone::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: radial-gradient(circle at var(--mouse-x, 50%) var(--mouse-y, 50%), rgba(187, 244, 68, 0.16) 0%, transparent 60%);
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

.dropzone:hover::before {
  opacity: 1;
}

.dropzone:hover {
  border-color: #7bb531;
  box-shadow: 0 16px 44px rgba(125, 181, 49, 0.14), var(--shadow-sm);
}

/* Animated Border Flow on Dragging Over */
.dropzone.dragging,
.dropzone.dragover {
  background: #fcfef8;
  border-color: transparent;
  transform: translateY(-4px) scale(1.01);
  box-shadow: 0 20px 50px rgba(123, 181, 49, 0.22), var(--shadow-sm);
}

.dropzone.dragging::after,
.dropzone.dragover::after {
  content: "";
  position: absolute;
  inset: -2px;
  border-radius: inherit;
  padding: 2px;
  background: linear-gradient(90deg, #7db531, var(--green), #55831f, var(--green));
  background-size: 300% 300%;
  animation: border-flow 2.4s linear infinite;
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
}

@keyframes border-flow {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.upload-icon-wrap,
.dropzone .upload-icon {
  width: 58px;
  height: 58px;
  background: #f1f7ea;
  border-radius: 16px;
  display: grid;
  place-items: center;
  color: #4b7a24;
  margin-bottom: 18px;
  transform: translateZ(15px);
  transition: transform 0.22s ease, background-color 0.2s ease;
}

.dropzone:hover .upload-icon-wrap,
.dropzone:hover .upload-icon,
.dropzone.dragging .upload-icon-wrap {
  transform: translateZ(25px) scale(1.1);
  background: #eaf4dd;
}

.upload-svg,
.dropzone .upload-icon svg {
  width: 26px;
  height: 26px;
}

.dropzone-title,
.dropzone h2 {
  font-size: 19px;
  font-weight: 700;
  letter-spacing: -0.4px;
  margin: 0 0 6px;
  color: var(--ink);
  transform: translateZ(10px);
}

.dropzone-or,
.dropzone p {
  font-size: 12.5px;
  color: var(--muted-light);
  margin: 0 0 16px;
  font-weight: 500;
  transform: translateZ(8px);
}

.browse-btn {
  padding: 12px 24px;
  font-size: 14px;
  border-radius: var(--radius-md);
  transform: translateZ(20px);
}

.text-button {
  color: #3f6620;
  font-weight: 700;
  text-decoration: underline;
  cursor: pointer;
  background: none;
  border: none;
  font-size: inherit;
}

.dropzone-specs,
.file-note {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 22px;
  font-size: 11.5px;
  color: var(--muted);
  font-weight: 500;
  flex-wrap: wrap;
  transform: translateZ(5px);
}

.spec-chip {
  background: var(--bg-subtle);
  padding: 2px 8px;
  border-radius: var(--radius-xs);
  color: var(--ink-secondary);
  font-weight: 600;
}

.spec-divider {
  color: var(--line-strong);
}

/* ==========================================================================
   4. Image Configuration Card
   ========================================================================== */
.config-card {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  padding: 22px;
  animation: card-appear 0.28s cubic-bezier(0.16, 1, 0.3, 1);
  transform-style: preserve-3d;
}

@keyframes card-appear {
  from { opacity: 0; transform: translateY(12px) scale(0.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.config-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 18px;
  border-bottom: 1px solid var(--line-light);
  gap: 16px;
}

.file-details {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.thumb-frame {
  width: 52px;
  height: 52px;
  border-radius: var(--radius-sm);
  background: var(--bg-subtle);
  border: 1px solid var(--line);
  overflow: hidden;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  box-shadow: var(--shadow-xs);
}

.config-thumbnail {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.file-meta-group {
  min-width: 0;
}

.file-meta-group strong,
.file-details strong {
  display: block;
  font-size: 14.5px;
  font-weight: 700;
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 400px;
}

.file-meta-group p,
.file-details p {
  font-size: 12px;
  color: var(--muted);
  margin-top: 2px;
}

.config-body {
  padding-top: 20px;
}

.scale-section {
  margin-bottom: 18px;
}

.section-title-wrap {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.scale-label {
  font-size: 12.5px;
  font-weight: 700;
  color: var(--ink);
  letter-spacing: -0.2px;
}

.scale-note {
  font-size: 11px;
  color: var(--muted);
}

.scale-selector {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.scale-pill {
  background: var(--surface-alt);
  border: 1.5px solid var(--line);
  border-radius: var(--radius-md);
  padding: 14px 18px;
  cursor: pointer;
  text-align: left;
  transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1);
  display: flex;
  flex-direction: column;
  gap: 3px;
  user-select: none;
}

.scale-pill:hover {
  background: var(--surface);
  border-color: var(--line-strong);
  transform: translateY(-1px);
}

.scale-pill.active {
  background: var(--green-surface);
  border-color: var(--green-border);
  box-shadow: 0 0 0 1px var(--green-border), 0 4px 14px rgba(125, 181, 49, 0.14);
}

.scale-num {
  font-size: 18px;
  font-weight: 800;
  color: var(--ink);
  letter-spacing: -0.5px;
}

.scale-pill.active .scale-num {
  color: var(--green-dark);
}

.scale-desc {
  font-size: 11.5px;
  font-weight: 600;
  color: var(--muted);
}

.scale-pill.active .scale-desc {
  color: #385e19;
}

.target-meta {
  background: var(--bg-subtle);
  border-radius: var(--radius-sm);
  padding: 10px 14px;
  font-size: 12px;
  color: var(--muted);
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.target-meta strong {
  color: var(--ink);
  font-family: var(--font-mono);
}

/* Error Alert Banner */
.error-banner {
  background: #fdf2f2;
  border: 1px solid #f8c8c8;
  border-radius: var(--radius-md);
  padding: 12px 16px;
  margin-bottom: 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: #991b1b;
  font-size: 13px;
  animation: card-appear 0.25s ease;
}

.error-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.retry-btn {
  background: #fee2e2;
  border-color: #fca5a5;
  color: #7f1d1d;
  padding: 5px 12px;
  font-size: 11.5px;
}

.retry-btn:hover {
  background: #fecaca;
  color: #7f1d1d;
}

/* Inline Progress Wrap (Backup/Compact View) */
.progress-wrap {
  margin-bottom: 20px;
  background: var(--surface-alt);
  border: 1px solid var(--line-light);
  border-radius: var(--radius-md);
  padding: 16px;
}

.progress-bar-track {
  height: 6px;
  background: #e6e8e0;
  border-radius: var(--radius-pill);
  overflow: hidden;
  margin-bottom: 12px;
  position: relative;
}

.progress-bar-fill {
  height: 100%;
  width: 0%;
  background: linear-gradient(90deg, #9fe620, var(--green));
  border-radius: var(--radius-pill);
  transition: width 0.3s ease;
  box-shadow: 0 0 10px var(--green-glow);
}

.progress-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12.5px;
  margin-bottom: 12px;
}

.progress-status {
  font-weight: 600;
  color: var(--ink-secondary);
}

.elapsed-timer {
  font-family: var(--font-mono);
  font-size: 11.5px;
  color: var(--muted);
  background: #eaede4;
  padding: 2px 7px;
  border-radius: var(--radius-xs);
}

.progress-stages {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 4px;
}

.stage-step {
  font-size: 10px;
  font-weight: 600;
  color: var(--muted-light);
  background: var(--bg);
  border: 1px solid var(--line);
  padding: 5px 2px;
  border-radius: var(--radius-xs);
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: all 0.2s ease;
}

.stage-step.active {
  background: var(--green-surface);
  border-color: var(--green-border);
  color: var(--green-dark);
  box-shadow: 0 0 0 1px var(--green-border);
}

.stage-step.done {
  background: #edf5e2;
  border-color: #9ecb5c;
  color: #3b601e;
}

.config-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
}

.enhance-btn {
  padding: 13px 28px;
  font-size: 14px;
  font-weight: 750;
}

.btn-sparkle {
  font-size: 12px;
}

.btn-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(22, 24, 20, 0.25);
  border-top-color: var(--ink);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  display: inline-block;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ==========================================================================
   5. Unique 3D Branded AI Loading Screen Experience
   ========================================================================== */
.processing-screen {
  background: rgba(14, 16, 12, 0.94);
  backdrop-filter: blur(28px);
  -webkit-backdrop-filter: blur(28px);
  border: 1px solid rgba(187, 244, 68, 0.22);
  border-radius: var(--radius-xl);
  box-shadow: 0 28px 80px rgba(0, 0, 0, 0.45), 0 0 50px rgba(187, 244, 68, 0.15);
  padding: 44px 28px 36px;
  color: #f7f9f3;
  animation: proc-appear 0.35s cubic-bezier(0.16, 1, 0.3, 1);
  position: relative;
  overflow: hidden;
  text-align: center;
}

@keyframes proc-appear {
  from { opacity: 0; transform: scale(0.97) translateY(14px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

.processing-card {
  max-width: 620px;
  margin: 0 auto;
  position: relative;
  z-index: 2;
}

/* 3D Geometric Ring & Floating Glass Orb Scene */
.gyro-scene {
  width: 220px;
  height: 220px;
  margin: 0 auto 28px;
  position: relative;
  perspective: 900px;
  transform-style: preserve-3d;
}

.gyro-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  border-radius: 50%;
  transform-style: preserve-3d;
  pointer-events: none;
}

.ring-outer {
  width: 210px;
  height: 210px;
  margin-top: -105px;
  margin-left: -105px;
  border: 2px solid rgba(187, 244, 68, 0.5);
  box-shadow: 0 0 24px rgba(187, 244, 68, 0.35), inset 0 0 16px rgba(187, 244, 68, 0.2);
  animation: gyro-spin-x 8s linear infinite;
}

.ring-middle {
  width: 165px;
  height: 165px;
  margin-top: -82.5px;
  margin-left: -82.5px;
  border: 2px solid rgba(150, 225, 20, 0.65);
  box-shadow: 0 0 20px rgba(150, 225, 20, 0.3);
  animation: gyro-spin-y 6s linear infinite reverse;
}

.ring-inner {
  width: 120px;
  height: 120px;
  margin-top: -60px;
  margin-left: -60px;
  border: 1.5px solid rgba(187, 244, 68, 0.8);
  box-shadow: 0 0 18px rgba(187, 244, 68, 0.4);
  animation: gyro-spin-z 10s linear infinite;
}

@keyframes gyro-spin-x {
  0% { transform: rotateX(65deg) rotateY(0deg) rotateZ(0deg); }
  100% { transform: rotateX(65deg) rotateY(360deg) rotateZ(360deg); }
}

@keyframes gyro-spin-y {
  0% { transform: rotateY(70deg) rotateX(0deg) rotateZ(0deg); }
  100% { transform: rotateY(70deg) rotateX(360deg) rotateZ(-360deg); }
}

@keyframes gyro-spin-z {
  0% { transform: rotateZ(45deg) rotateX(0deg) rotateY(0deg); }
  100% { transform: rotateZ(45deg) rotateX(360deg) rotateY(360deg); }
}

/* Floating Glass Orb in Center */
.glass-orb {
  width: 82px;
  height: 82px;
  position: absolute;
  top: 50%;
  left: 50%;
  margin-top: -41px;
  margin-left: -41px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 35%, 
              rgba(255, 255, 255, 0.5) 0%, 
              rgba(187, 244, 68, 0.3) 35%, 
              rgba(25, 45, 12, 0.85) 85%);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1.5px solid rgba(255, 255, 255, 0.35);
  box-shadow: 0 0 35px rgba(187, 244, 68, 0.55), 
              inset 0 0 16px rgba(255, 255, 255, 0.3),
              0 14px 28px rgba(0, 0, 0, 0.45);
  display: grid;
  place-items: center;
  animation: orb-levitate 3.5s ease-in-out infinite alternate;
  z-index: 5;
}

@keyframes orb-levitate {
  0% { transform: translate3d(0, -6px, 0) scale(0.98); }
  100% { transform: translate3d(0, 6px, 0) scale(1.02); }
}

.orb-highlight {
  position: absolute;
  top: 10px;
  left: 14px;
  width: 24px;
  height: 14px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.65);
  filter: blur(2px);
  transform: rotate(-30deg);
}

.orb-core {
  display: flex;
  align-items: center;
  justify-content: center;
}

.orb-mark {
  color: var(--green);
  font-size: 32px;
  line-height: 1;
  text-shadow: 0 0 16px var(--green);
  animation: mark-pulse 2.2s ease-in-out infinite alternate;
}

@keyframes mark-pulse {
  0% { transform: scale(0.95); opacity: 0.9; }
  100% { transform: scale(1.15); opacity: 1; filter: drop-shadow(0 0 10px var(--green)); }
}

/* Floating Micro-Particles */
.particles-field {
  position: absolute;
  inset: -20px;
  pointer-events: none;
}

.particle {
  position: absolute;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--green);
  box-shadow: 0 0 8px var(--green);
  opacity: 0.6;
}

.p1 { top: 20%; left: 15%; animation: particle-drift 4.2s ease-in-out infinite 0.2s; }
.p2 { top: 30%; right: 18%; animation: particle-drift 5.1s ease-in-out infinite 0.7s; }
.p3 { bottom: 25%; left: 22%; animation: particle-drift 3.8s ease-in-out infinite 1.2s; }
.p4 { bottom: 15%; right: 25%; animation: particle-drift 4.6s ease-in-out infinite 1.6s; }
.p5 { top: 10%; right: 35%; animation: particle-drift 4.8s ease-in-out infinite 0.4s; }
.p6 { bottom: 35%; right: 10%; animation: particle-drift 3.6s ease-in-out infinite 0.9s; }
.p7 { top: 40%; left: 10%; animation: particle-drift 5.4s ease-in-out infinite 1.4s; }
.p8 { bottom: 10%; left: 40%; animation: particle-drift 4.4s ease-in-out infinite 1.9s; }

@keyframes particle-drift {
  0% { transform: translate3d(0, 0, 0) scale(1); opacity: 0.3; }
  50% { transform: translate3d(12px, -18px, 0) scale(1.4); opacity: 0.9; }
  100% { transform: translate3d(-10px, -36px, 0) scale(0.8); opacity: 0.2; }
}

/* Hologram Scanning Reconstruction Frame */
.hologram-scan-stage {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}

.hologram-frame {
  position: relative;
  width: 140px;
  height: 94px;
  border-radius: 10px;
  border: 1px solid rgba(187, 244, 68, 0.4);
  overflow: hidden;
  background: #000000;
  box-shadow: 0 0 20px rgba(187, 244, 68, 0.2);
}

.hologram-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0.85;
  filter: contrast(1.1) saturate(1.2);
}

.scan-beam {
  position: absolute;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, transparent, #ffffff, var(--green), transparent);
  box-shadow: 0 0 14px var(--green), 0 0 4px #ffffff;
  animation: scan-vertical 2.2s ease-in-out infinite alternate;
  z-index: 3;
}

.scan-grid-overlay {
  position: absolute;
  inset: 0;
  background-image: 
    linear-gradient(rgba(187, 244, 68, 0.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(187, 244, 68, 0.1) 1px, transparent 1px);
  background-size: 8px 8px;
  pointer-events: none;
  z-index: 2;
}

.scan-glow-line {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(187, 244, 68, 0.08) 0%, transparent 60%);
  pointer-events: none;
}

@keyframes scan-vertical {
  0% { top: 0%; opacity: 0.8; }
  100% { top: 96%; opacity: 1; }
}

/* Processing Brand & Titles */
.proc-brand-line {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-bottom: 12px;
}

.proc-brand-text {
  font-weight: 800;
  font-size: 16px;
  color: #ffffff;
  letter-spacing: -0.4px;
}

.proc-brand-text .dot {
  color: var(--green);
}

.proc-device-pill {
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.5px;
  color: var(--green);
  background: rgba(187, 244, 68, 0.12);
  border: 1px solid rgba(187, 244, 68, 0.35);
  padding: 2px 8px;
  border-radius: var(--radius-pill);
}

.proc-title {
  font-size: 22px;
  font-weight: 800;
  color: #ffffff;
  letter-spacing: -0.5px;
  margin-bottom: 6px;
  min-height: 28px;
}

.proc-desc {
  font-size: 13px;
  color: #a7ab9f;
  margin-bottom: 20px;
  min-height: 20px;
}

/* Sleek Indeterminate Progress Rail */
.proc-rail-track {
  width: 100%;
  height: 5px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-pill);
  position: relative;
  overflow: hidden;
  margin-bottom: 16px;
}

.proc-rail-bar {
  position: absolute;
  height: 100%;
  width: 35%;
  background: linear-gradient(90deg, transparent, var(--green), #ffffff, var(--green), transparent);
  box-shadow: 0 0 16px var(--green);
  border-radius: var(--radius-pill);
  animation: rail-travel 1.8s cubic-bezier(0.4, 0, 0.2, 1) infinite;
}

@keyframes rail-travel {
  0% { left: -35%; }
  100% { left: 100%; }
}

/* Stats Row (Live Timer & Scale) */
.proc-stats-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  margin-bottom: 22px;
  padding: 0 4px;
}

.proc-timer {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #c7cbc0;
}

.timer-live-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--green);
  box-shadow: 0 0 6px var(--green);
  animation: pulse-dot 1.8s infinite;
}

.proc-timer strong {
  font-family: var(--font-mono);
  color: #ffffff;
}

.proc-target-scale {
  color: var(--green);
  font-weight: 600;
  font-size: 11.5px;
}

/* Actual Processing Stages Strip */
.proc-stages-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 6px;
  margin-bottom: 24px;
}

.proc-step {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-sm);
  padding: 8px 4px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  transition: all 0.25s ease;
}

.proc-step .step-num {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.15);
  color: #a7ab9f;
  font-size: 10px;
  font-weight: 700;
  display: grid;
  place-items: center;
}

.proc-step .step-label {
  font-size: 10px;
  font-weight: 600;
  color: #8c9085;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.proc-step.active {
  background: rgba(187, 244, 68, 0.14);
  border-color: rgba(187, 244, 68, 0.6);
  box-shadow: 0 0 16px rgba(187, 244, 68, 0.25);
  transform: translateY(-2px);
}

.proc-step.active .step-num {
  background: var(--green);
  color: var(--ink);
  box-shadow: 0 0 10px var(--green-glow);
}

.proc-step.active .step-label {
  color: #ffffff;
}

.proc-step.done {
  background: rgba(125, 181, 49, 0.1);
  border-color: rgba(125, 181, 49, 0.4);
}

.proc-step.done .step-num {
  background: #55831f;
  color: #ffffff;
}

.proc-step.done .step-label {
  color: #c7cbc0;
}

.proc-cancel-btn {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.16);
  color: #d1d5c9;
  border-radius: var(--radius-pill);
  padding: 8px 20px;
  font-size: 12px;
  font-weight: 600;
  transition: all 0.18s ease;
}

.proc-cancel-btn:hover {
  background: rgba(239, 68, 68, 0.18);
  border-color: rgba(239, 68, 68, 0.4);
  color: #fca5a5;
  transform: translateY(-1px);
}

/* ==========================================================================
   6. Comparison Workspace (Viewer State)
   ========================================================================== */
.editor {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-3d);
  padding: 20px;
  animation: result-reveal 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes result-reveal {
  from { opacity: 0; transform: scale(0.97) translateY(16px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

.editor-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--line-light);
  gap: 16px;
}

.editor-titles strong,
.editor-head strong {
  font-size: 15px;
  font-weight: 700;
  color: var(--ink);
  display: block;
}

.editor-titles p,
.editor-head p {
  font-size: 12px;
  color: var(--muted);
  margin-top: 2px;
}

/* Neutral Preview Stage Canvas with Realistic Depth */
.preview-stage {
  position: relative;
  background: var(--stage-bg);
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  overflow: hidden;
  margin-bottom: 18px;
  min-height: 420px;
  display: flex;
  align-items: center;
  justify-content: center;
  user-select: none;
  box-shadow: var(--shadow-3d);
}

/* Floating Zoom & Display Toolbar */
.zoom-toolbar {
  position: absolute;
  top: 14px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 20;
  background: rgba(255, 255, 255, 0.94);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: var(--radius-pill);
  padding: 4px 6px;
  display: flex;
  align-items: center;
  gap: 2px;
  box-shadow: var(--shadow-float);
}

.zoom-btn {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-pill);
  display: grid;
  place-items: center;
  font-size: 14px;
  font-weight: 700;
  color: var(--ink-secondary);
  transition: all 0.15s ease;
}

.zoom-btn:hover {
  background: #f0f2eb;
  color: var(--ink);
}

.zoom-text-btn {
  width: auto;
  padding: 0 10px;
  font-size: 11.5px;
  font-weight: 650;
}

.zoom-text-btn.active {
  background: var(--green);
  color: var(--ink);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.zoom-divider {
  width: 1px;
  height: 14px;
  background: var(--line);
  margin: 0 3px;
}

.zoom-level {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  color: var(--ink-secondary);
  padding: 0 6px;
  min-width: 44px;
  text-align: center;
}

/* Preview Wrap (Image container scaled & panned) */
.preview-wrap {
  position: relative;
  max-width: 100%;
  max-height: 580px;
  display: inline-block;
  line-height: 0;
  transform-origin: center center;
  touch-action: none;
}

.preview-wrap img {
  display: block;
  max-width: 100%;
  max-height: 580px;
  width: auto;
  height: auto;
  user-select: none;
  -webkit-user-drag: none;
}

.after-pane {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  clip-path: polygon(0 0, 50% 0, 50% 100%, 0 100%);
  z-index: 2;
}

.after-pane img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: fill;
}

/* Draggable Comparison Line & Knob */
.slider-line {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 50%;
  width: 2px;
  background: #ffffff;
  transform: translateX(-50%);
  pointer-events: none;
  z-index: 5;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
}

.slider-knob,
.slider-line span {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 34px;
  height: 34px;
  background: #ffffff;
  border-radius: 50%;
  box-shadow: 0 3px 14px rgba(0, 0, 0, 0.35);
  display: grid;
  place-items: center;
  font-size: 13px;
  color: var(--ink);
  font-weight: 800;
  border: 2px solid #ffffff;
  transition: transform 0.15s ease;
}

.compare-slider {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: ew-resize;
  z-index: 10;
  margin: 0;
}

/* Labels */
.preview-label {
  position: absolute;
  bottom: 14px;
  font-size: 10.5px;
  font-weight: 750;
  letter-spacing: 0.6px;
  padding: 5px 10px;
  border-radius: var(--radius-sm);
  z-index: 4;
  pointer-events: none;
  box-shadow: var(--shadow-sm);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.before-label {
  left: 14px;
  background: rgba(22, 24, 20, 0.78);
  color: #ffffff;
}

.after-label {
  right: 14px;
  background: rgba(255, 255, 255, 0.94);
  color: var(--green-dark);
  border: 1px solid rgba(125, 181, 49, 0.45);
}

/* Comprehensive Output Metadata Strip */
.metadata-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  background: var(--bg-subtle);
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  padding: 14px 16px;
  margin-bottom: 18px;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.meta-label {
  font-size: 10.5px;
  font-weight: 600;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.meta-val {
  font-size: 13px;
  font-weight: 700;
  color: var(--ink);
  font-family: var(--font-mono);
}

.highlight-val {
  color: #385f1a;
  background: var(--green-surface);
  display: inline-block;
  padding: 0 4px;
  border-radius: 3px;
}

/* Editor Action Bar */
.editor-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.scale-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--ink-secondary);
}

.download-btn {
  padding: 13px 28px;
  font-size: 14px;
  font-weight: 750;
  border-radius: var(--radius-md);
}

.btn-download-arrow {
  font-size: 14px;
  font-weight: 800;
}

/* Fullscreen Mode */
:fullscreen .preview-stage {
  border-radius: 0;
  border: none;
  min-height: 100vh;
  margin: 0;
}

:fullscreen .preview-wrap img {
  max-height: 90vh;
}

/* ==========================================================================
   7. Buttons & 3D Interactive Press Depth
   ========================================================================== */
.primary-btn {
  border: 0;
  border-radius: var(--radius-md);
  background: var(--green);
  color: var(--ink);
  padding: 12px 22px;
  font-size: 13.5px;
  font-weight: 750;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-shadow: 0 4px 14px var(--green-glow), 0 2px 0 #5f8d22;
  transform: translateY(0);
  transition: all 0.16s cubic-bezier(0.16, 1, 0.3, 1);
  position: relative;
}

.primary-btn:hover {
  background: var(--green-hover);
  transform: translateY(-2px);
  box-shadow: 0 7px 22px var(--green-glow), 0 3px 0 #5f8d22;
}

.primary-btn:active {
  transform: translateY(2px) scale(0.985);
  box-shadow: 0 1px 4px var(--green-glow), 0 0 0 #5f8d22;
}

.primary-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.quiet-btn {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  padding: 8px 14px;
  font-size: 12.5px;
  cursor: pointer;
  transition: all 0.16s ease;
  font-weight: 600;
  color: var(--ink-secondary);
  box-shadow: var(--shadow-xs);
}

.quiet-btn:hover {
  background: var(--surface-alt);
  border-color: var(--line-strong);
  color: var(--ink);
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

.quiet-btn:active {
  transform: translateY(1px);
}

.hidden {
  display: none !important;
}

/* ==========================================================================
   8. Feature Cards Section (Interactive 3D Tilt)
   ========================================================================== */
.benefits {
  max-width: 1000px;
  margin: 54px auto 36px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  width: 100%;
  position: relative;
  z-index: 1;
  perspective: 1000px;
}

.benefit-card,
.benefits article {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  padding: 24px;
  box-shadow: var(--shadow-sm);
  transform-style: preserve-3d;
  transition: transform 0.22s cubic-bezier(0.16, 1, 0.3, 1), 
              box-shadow 0.22s cubic-bezier(0.16, 1, 0.3, 1), 
              border-color 0.2s ease;
  display: flex;
  flex-direction: column;
  will-change: transform;
}

.benefit-card:hover,
.benefits article:hover {
  border-color: #8cbd42;
  box-shadow: 0 16px 36px rgba(22, 24, 20, 0.08), 0 0 20px rgba(187, 244, 68, 0.12);
}

.benefit-icon {
  width: 44px;
  height: 44px;
  background: var(--green-surface);
  border: 1px solid rgba(125, 181, 49, 0.3);
  border-radius: 12px;
  display: grid;
  place-items: center;
  font-size: 20px;
  margin-bottom: 16px;
  flex-shrink: 0;
  transform: translateZ(12px);
  transition: transform 0.2s ease;
}

.benefit-card:hover .benefit-icon {
  transform: translateZ(20px) scale(1.08);
}

.benefit-card h3,
.benefits article h3 {
  font-size: 15.5px;
  font-weight: 700;
  margin: 0 0 8px;
  color: var(--ink);
  letter-spacing: -0.2px;
  transform: translateZ(8px);
}

.benefit-card p,
.benefits article p {
  font-size: 13px;
  line-height: 1.6;
  color: var(--muted);
  margin: 0;
  transform: translateZ(4px);
}

/* ==========================================================================
   9. About & FAQ Sections
   ========================================================================== */
.about-section,
.how-section,
.faq-section {
  max-width: 820px;
  margin: 48px auto;
  width: 100%;
  position: relative;
  z-index: 1;
}

.section-badge,
.eyebrow {
  font-size: 10.5px;
  font-weight: 750;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  color: #3f6620;
  margin-bottom: 8px;
}

.about-section h2,
.how-section h2,
.faq-section h2 {
  font-size: 26px;
  font-weight: 800;
  letter-spacing: -0.6px;
  margin: 0 0 24px;
  color: var(--ink);
}

.about-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.about-col h4 {
  font-size: 15px;
  font-weight: 700;
  margin: 0 0 8px;
  color: var(--ink);
}

.about-col p {
  font-size: 13px;
  color: var(--muted);
  line-height: 1.65;
  margin: 0;
}

details {
  border-bottom: 1px solid var(--line);
  padding: 16px 0;
}

details summary {
  font-size: 14.5px;
  font-weight: 650;
  cursor: pointer;
  list-style: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--ink);
  transition: color 0.15s ease;
  user-select: none;
}

details summary::-webkit-details-marker {
  display: none;
}

details summary::after {
  content: "+";
  font-size: 18px;
  font-weight: 400;
  color: var(--muted);
  transition: transform 0.2s ease;
  flex-shrink: 0;
  margin-left: 12px;
}

details[open] summary::after {
  transform: rotate(45deg);
}

details p {
  font-size: 13px;
  line-height: 1.65;
  color: var(--muted);
  margin: 10px 0 0;
}

/* ==========================================================================
   10. Footer
   ========================================================================== */
.footer,
footer {
  background: var(--surface);
  border-top: 1px solid var(--line);
  margin-top: 60px;
  padding: 44px 24px 28px;
  position: relative;
  z-index: 1;
}

.footer-inner {
  max-width: 1080px;
  margin: 0 auto;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 36px;
}

.footer-brand {
  max-width: 360px;
}

.footer-desc {
  font-size: 12.5px;
  color: var(--muted);
  margin: 10px 0 0;
  line-height: 1.6;
}

.footer-links-group {
  display: flex;
  gap: 48px;
}

.footer-col {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.footer-col h5 {
  font-size: 11px;
  font-weight: 750;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  color: var(--ink);
  margin-bottom: 4px;
}

.footer-col a {
  font-size: 12.5px;
  color: var(--muted);
}

.footer-col a:hover {
  color: var(--ink);
}

.footer-col span {
  font-size: 12.5px;
  color: var(--muted-light);
}

.footer-bottom {
  max-width: 1080px;
  margin: 28px auto 0;
  padding-top: 18px;
  border-top: 1px solid var(--line-light);
  font-size: 11.5px;
  color: var(--muted-light);
  text-align: center;
}

/* ==========================================================================
   11. Responsive Breakpoints & Motion Settings
   ========================================================================== */
@media (max-width: 900px) {
  .benefits {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .about-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .metadata-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .topbar-inner {
    padding: 12px 16px;
  }

  .brand-descriptor {
    display: none;
  }

  .nav-links {
    gap: 4px;
  }

  .nav-links a,
  .topbar nav a,
  .nav-link {
    font-size: 12px;
    padding: 5px 8px;
  }

  .privacy-pill {
    padding: 4px 8px;
    font-size: 10px;
    margin-left: 2px;
  }

  .content-container,
  .main-container {
    padding: 0 16px;
  }

  .hero-section {
    padding: 28px 12px 18px;
  }

  .dropzone {
    min-height: 250px;
    padding: 32px 16px;
  }

  .scale-selector {
    grid-template-columns: 1fr;
    gap: 8px;
  }

  .progress-stages,
  .proc-stages-grid {
    grid-template-columns: 1fr;
    gap: 4px;
  }

  .footer-inner {
    flex-direction: column;
    gap: 24px;
  }

  .footer-links-group {
    width: 100%;
    justify-content: space-between;
  }
}

@media (max-width: 480px) {
  .zoom-toolbar {
    padding: 2px 4px;
    gap: 1px;
    width: 94%;
    justify-content: space-between;
  }

  .zoom-btn {
    width: 24px;
    height: 24px;
    font-size: 12px;
  }

  .zoom-text-btn {
    padding: 0 6px;
    font-size: 10px;
  }

  .metadata-grid {
    grid-template-columns: 1fr;
  }

  .editor-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .download-btn {
    width: 100%;
  }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }

  .gyro-ring,
  .glass-orb,
  .particle,
  .scan-beam,
  .proc-rail-bar,
  .ambient-orb {
    animation: none !important;
  }

  .dropzone,
  .benefit-card {
    transform: none !important;
  }
}
"""

with open("static/style.css", "w") as f:
    f.write(css_content)

print(f"Successfully wrote {len(css_content)} characters to static/style.css")
assert css_content.count("{") == css_content.count("}"), "Brace count mismatch!"
print(f"Brace check passed: {css_content.count('{')} braces.")
