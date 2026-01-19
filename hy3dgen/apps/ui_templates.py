from pathlib import Path

HTML_TEMPLATE_MODEL_VIEWER = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>
    <style>
        :root {
            --bg-app: #090B1F;
            --primary-500: #6366f1;
            --text-error: #ef4444;
            --bg-error: rgba(0,0,0,0.9);
            --font-family: ui-sans-serif, system-ui, sans-serif;
        }
        body { 
            margin: 0; 
            background: var(--bg-app);
            height: 100vh; 
            width: 100vw; 
            overflow: hidden; 
            font-family: var(--font-family);
        }
        model-viewer {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%; 
            height: 100%; 
            background: transparent;
            --progress-bar-color: var(--primary-500); 
        }
        model-viewer:focus {
            outline: none; 
        }
        model-viewer:focus-visible {
            outline: 2px solid var(--primary-500);
            outline-offset: 2px;
            border-radius: 4px;
        }
        model-viewer::part(default-progress-bar) {
            height: 4px;
            background-color: var(--primary-500);
        }
        #error-log {
            position: absolute;
            top: 10px;
            left: 10px;
            color: var(--text-error);
            background: var(--bg-error);
            padding: 12px;
            border-radius: 6px;
            display: none;
            z-index: 100;
            font-size: 14px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
            max-width: 90%;
        }
    </style>
</head>
<body>
    <div id="error-log" role="alert" aria-live="assertive"></div>
    <model-viewer src="#src#" 
                  alt="Generated 3D Model View" 
                  aria-label="Interactive 3D model viewer. Use mouse or touch to rotate, zoom, and pan."
                  auto-rotate 
                  camera-controls 
                  bounds="tight" 
                  min-field-of-view="10deg"
                  max-field-of-view="45deg"
                  interpolation-quality="high"
                  shadow-intensity="1" 
                  exposure="1.0" 
                  tone-mapping="neutral"
                  ar
                  ar-modes="webxr scene-viewer quick-look"
                  tabindex="0">
        <div slot="progress-bar" style="display: none;"></div>
    </model-viewer>
    <script>
        const modelViewer = document.querySelector('model-viewer');
        const errorLog = document.getElementById('error-log');

        modelViewer.addEventListener('error', (event) => {
            console.error("ModelViewer Error:", event);
            errorLog.style.display = 'block';
            errorLog.innerText = "Error loading 3D model: " + (event.detail.message || "Unknown error detected.");
        });

        modelViewer.addEventListener('load', () => {
            console.log("Model loaded successfully");
            const model = modelViewer.model;
            if (model && model.materials) {
                model.materials.forEach(material => {
                    // Fix for meshes that might appear black if baseColor is missing/invalid
                    if (material.pbrMetallicRoughness && !material.pbrMetallicRoughness.baseColorTexture) {
                        material.pbrMetallicRoughness.setBaseColorFactor([1.0, 1.0, 1.0, 1.0]);
                        material.pbrMetallicRoughness.setRoughnessFactor(0.5);
                        material.pbrMetallicRoughness.setMetallicFactor(0.0);
                    }
                    material.setDoubleSided(true);
                });
            }
        });
        
        // Accessibility: Add keyboard visual focus helper if needed, 
        // though standard outlines usually work with tabindex=0
    </script>
</body>
</html>
"""

HTML_PLACEHOLDER = """
<div class='empty-placeholder'>
  <div class='empty-placeholder-icon'>
    <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3L2 12h3v8h6v-6h2v6h6v-8h3L12 3z"></path></svg>
  </div>
  <h3 class='empty-placeholder-title'>Ready to Create</h3>
  <p class='empty-placeholder-text'>Configure your prompt and settings on the left, then click Generate.</p>
</div>
"""

HTML_PROCESSING = """
<div class="processing-container">
    <div class="cube-wrapper">
        <div class="cube">
            <div class="face front"></div>
            <div class="face back"></div>
            <div class="face left"></div>
            <div class="face right"></div>
            <div class="face top"></div>
            <div class="face bottom"></div>
        </div>
        <div class="scanner-line"></div>
    </div>
    <h3 class="processing-title">Archeon 3D Core</h3>
    <p class="processing-status">Synthesizing Geometry...</p>
</div>
"""

# Embedded AEGIS UI Theme (Pixel Perfect Fit-to-Screen)
CSS_STYLES = """
/* AEGIS UI Reset */
:root {
    --bg-app: #090B1F;
    --primary-500: #6366f1;
    --surface-100: #1a1b26;
    --surface-200: #24283b;
    --text-main: #c0caf5;
}

body, .gradio-container {
    background-color: var(--bg-app) !important;
    color: var(--text-main) !important;
    margin: 0 !important;
    padding: 0 !important;
    max-width: 100% !important;
    height: 100vh !important;
    overflow-x: hidden !important; /* Prevent horizontal scrollbars */
    overflow-y: hidden !important; /* Prevent double scrollbars */
}

/* Scrollbar Styling */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: transparent;
}
::-webkit-scrollbar-thumb {
    background: var(--surface-200);
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: var(--primary-500);
}

/* Stop Button Styling */
button.stop {
    background-color: #ef4444 !important;
    color: white !important;
    border: 1px solid #dc2626 !important;
    text-align: center !important;
    padding-left: 20px !important;
    padding-right: 20px !important;
}
button.stop:hover {
    background-color: #dc2626 !important;
}

/* Main Layout Fixes */
/* Main Layout Fixes - Flexbox Architecture */
.main-row {
    height: calc(100vh - 60px) !important; 
    gap: 0 !important;
    overflow: hidden !important; /* Block all outer scroll */
}

/* Left Column: converts to Flex Container to Dock Footer */
.left-col {
    height: 100% !important;
    padding: 16px !important;
    display: flex !important;
    flex-direction: column !important;
    overflow-y: auto !important; /* Allow scrolling if content exceeds height */
    overflow-x: hidden !important;
}

.right-col {
    height: 100% !important;
    padding: 0 !important; /* Start with zero to build up */
    display: flex !important;
    flex-direction: column !important;
    overflow: hidden !important;
    position: relative !important;
}

/* Force Gradio Tabs and their containers to fill height but respect siblings */
.right-col .tabs {
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 auto !important; /* Fill available space */
    min-height: 0 !important; /* Allow shrinking */
}

.right-col .tabitem {
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 auto !important;
    min-height: 0 !important;
}

/* Force Tab Content to Fill Space */
.right-col > .form, 
.right-col .tabarea, 
.right-col .tabitem, 
.right-col .group,
.right-col .form {
    height: auto !important; /* Allow sharing space with footer */
    min-height: 0 !important; /* Critical for Flexbox scrolling */
    flex: 1 1 0% !important;
    display: flex !important;
    flex-direction: column !important;
}

/* Specific Height for Output Containers */
#gen_output_container {
    height: 100% !important;
    flex: 1 1 auto !important;
    display: flex !important;
    flex-direction: column !important;
    overflow: hidden !important;
    padding: 0 !important;
    position: relative !important; /* Anchor for absolute viewer */
}

#gen_output_container > .form {
    height: 100% !important;
    flex: 1 !important;
    display: flex !important;
    flex-direction: column !important;
}

#model_3d_viewer {
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
    bottom: 0 !important;
    display: flex !important;
    flex-direction: column !important;
    z-index: 10 !important;
}

/* Ensure Iframe container (Gradio HTML) fills space recursively but allows siblings like footer */
#model_3d_viewer,
#model_3d_viewer > .prose, 
#model_3d_viewer > .prose > div,
#model_3d_viewer > div,
#model_3d_viewer iframe {
    width: 100% !important;
    height: 100% !important;
    max-width: none !important;
    display: flex !important;
    flex-direction: column !important;
    overflow: hidden !important;
    border: none !important;
    margin: 0 !important;
    padding: 0 !important;
}


/* Scroll Area: Takes all available space */
.scroll-area {
    flex: 1 1 auto !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
    padding-right: 8px !important; /* Space for scrollbar */
    min-height: 0 !important; /* Firefox flex fix */
}

/* Footer Area: Docked via Flexbox */
.footer-area {
    flex: 0 0 auto !important;
    padding: 12px 16px !important; 
    border-top: 1px solid var(--surface-200) !important;
    background: var(--bg-app) !important;
    z-index: 50 !important;
    margin-top: auto !important; /* Force to bottom of flex container */
    width: 100% !important; /* Ensure full width */
    box-sizing: border-box !important;
}

/* Panel Containers */
.panel-container {
    background: var(--surface-100);
    border: 1px solid var(--surface-200);
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 12px;
}

/* Compact Tabs */
/* Nuclear Option for Settings Tabs: Force Visibility */
#gen_settings_container {
    padding: 0 !important;
    width: 100% !important;
    overflow: visible !important;
    display: flex !important;
    flex-direction: column !important;
    flex-grow: 1 !important;
}

#gen_settings_container > .tabs {
    width: 100% !important;
    overflow: visible !important;
    display: flex !important;
    flex-direction: column !important;
    flex-grow: 1 !important;
    padding: 0 !important;
    margin: 0 !important;
    border: none !important;
}

/* Force nav bar to be a single single flex row, no wrapping */
#gen_settings_container .tab-nav {
    display: flex !important;
    flex-wrap: nowrap !important;
    width: 100% !important;
    min-width: 100% !important;
    overflow: visible !important;
    margin-top: 12px !important;
    border-bottom: 1px solid var(--surface-200) !important;
    padding: 0 !important;
    gap: 0 !important;
}

/* Force buttons to share space equally and shrink indefinitely */
#gen_settings_container .tab-nav button {
    flex: 1 1 0px !important;
    min-width: 0 !important; /* Allow shrinking to nothing if needed */
    width: auto !important;
    max-width: none !important;
    padding: 6px 0 !important;
    margin: 0 !important;
    font-size: 12px !important;
    overflow: hidden !important;
    white-space: nowrap !important;
    text-overflow: clip !important; /* Prevent ellipsis logic? */
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    border: none !important;
    border-radius: 4px 4px 0 0 !important;
}

/* Ensure selected state is still visible */
#gen_settings_container .tab-nav button.selected {
    border-bottom: 2px solid var(--primary-500) !important;
    background: rgba(99, 102, 241, 0.05) !important;
    color: var(--primary-500) !important;
    font-weight: 600 !important;
}

/* Hide the overflow dropdown button if it tries to spawn */
#gen_settings_container .tab-nav button.options {
    display: none !important;
    width: 0 !important;
    height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    overflow: hidden !important;
}

/* Ensure content fills space */
#gen_settings_container .tabitem {
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    padding-top: 8px !important;
    padding-bottom: 8px !important;
    border: none !important;
    height: auto !important;
}

/* 
   CRITICAL FIX: Gradio toggles visibility via inline style="display: none". 
   We must ensuring our CSS does not override this with !important.
   However, we need !important to force Flexbox when it IS visible.
   Solution: Explicitly force hide if Gradio tries to hide it.
*/
#gen_settings_container .tabitem[style*="display: none"] {
    display: none !important;
}

#gen_settings_container .tabitem[style*="display: block"] {
    display: flex !important;
}

/* Fallback if Gradio uses classes */
#gen_settings_container .tabitem.hidden {
    display: none !important;
}

#gen_settings_container .tabitem > .form, 
#gen_settings_container .tabitem > .gr-group {
    flex-grow: 1 !important;
    border: none !important;
    background: transparent !important;
}

/* Tab labels polish */
.tab-nav, .tab-container {
    border-bottom: 1px solid var(--surface-200) !important;
    display: flex !important;
    width: 100% !important;
    margin-top: 12px !important;
}
.tab-nav button, .tab-container button {
    flex: 1 1 0% !important;
    font-size: 1.05em !important;
    font-weight: 500 !important;
    padding: 10px 4px !important;
    transition: all 0.2s ease !important;
    white-space: nowrap !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
}
button.selected {
    border-bottom: 3px solid var(--primary-500) !important;
    color: var(--primary-500) !important;
    background: rgba(99, 102, 241, 0.05) !important;
}

/* Model Viewer Iframe Polish */
iframe {
    width: 100% !important; 
    height: 100% !important; 
    border-radius: 8px; 
    background: #000;
}

/* Footer Polish */
.footer-divider {
    margin: 12px 0 !important;
    border-color: var(--surface-200) !important;
}
.footer-text {
    text-align: center;
    font-size: 0.8em;
    opacity: 0.6;
}

/* Input Compaction */
.block.form {
    background: transparent !important;
    border: none !important;
}

/* Prompt Container Standardization */
.prompt-container {
    height: 320px !important; /* Fixed height for consistency */
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    overflow: hidden !important;
}

/* Ensure images inside prompt container don't overflow */
.prompt-container .gradio-image {
    max-height: 100% !important;
}

/* Sticky Action Buttons */
.sticky-actions {
    position: relative !important; /* Reverting sticky to ensure visibility */
    /* bottom: 0 !important; REMOVED */
    background: var(--bg-app) !important;
    z-index: 100 !important;
    padding-top: 10px !important;
    padding-bottom: 0px !important;
    border-top: 1px solid var(--surface-200) !important;
}

/* Fix "Missing Icon" squares in block labels */
.block-label img, .block-title img {
    display: none !important;
}

/* Empty Placeholder Polish */
.empty-placeholder {
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    height: 100% !important;
    width: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    opacity: 0.8 !important; /* Increased visibility */
    text-align: center !important;
    pointer-events: none !important; /* Let clicks pass through if needed */
    z-index: 50 !important; /* Ensure visibility */
}
.empty-placeholder-icon svg {
    width: 64px;
    height: 64px;
    margin-bottom: 16px;
    animation: floatIcon 3s ease-in-out infinite; /* Added Animation */
    filter: drop-shadow(0 0 10px rgba(99, 102, 241, 0.3));
}
.empty-placeholder-title {
    font-size: 1.5em;
    font-weight: 600;
    margin-bottom: 8px;
    color: var(--text-main);
}
.empty-placeholder-text {
    font-size: 0.9em;
    color: var(--text-main);
    opacity: 0.7;
}

@keyframes floatIcon {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
}

/* Custom Archeon Progress Bar */
.archeon-progress-container {
    width: calc(100% - 32px);
    margin: 4px 16px !important;
    background: var(--surface-200);
    border-radius: 4px;
    height: 20px;
    position: relative;
    overflow: hidden;
    z-index: 60; /* Above viewer */
}

.archeon-progress-fill {
    background: var(--primary-500);
    height: 100%;
    width: 0%;
    transition: width 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: flex-end;
}

.archeon-progress-text {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    color: white;
    font-weight: bold;
    text-shadow: 0 1px 2px rgba(0,0,0,0.8);
    z-index: 10;
    pointer-events: none;
}

/* Hide Default Gradio Footer, API Link, and Framework Metadata */
footer, 
.gradio-container footer, 
#api-link, 
.show-api, 
.meta-text, 
.built-with,
.gr-pro-branding {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
}

/* Hide Flagging buttons if they leak */
.flag-button, 
button.secondary.flag {
    display: none !important;
}

/* Progress Bar Container Visibility */
#progress_bar_container {
    display: flex !important;
    flex-direction: column !important;
    min-height: 24px !important;
    width: 100% !important;
    z-index: 500 !important;
    margin-top: 8px !important;
    margin-bottom: 8px !important;
    background: transparent !important;
}

/* Premium 3D Processing Animation */
.processing-container {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 1000 !important; /* Force on top of viewer */
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: radial-gradient(circle at center, rgba(99, 102, 241, 0.1) 0%, transparent 70%);
    pointer-events: none; /* Allow clicks to pass if needed, though usually blocking is fine */
}

.cube-wrapper {
    width: 100px;
    height: 100px;
    perspective: 800px;
    position: relative;
    margin-bottom: 30px;
}

.cube {
    width: 60px;
    height: 60px;
    position: absolute;
    top: 20px;
    left: 20px;
    transform-style: preserve-3d;
    animation: rotateCube 4s infinite linear, pulseCube 2s infinite ease-in-out;
}

.face {
    position: absolute;
    width: 60px;
    height: 60px;
    background: rgba(99, 102, 241, 0.2);
    border: 1px solid rgba(99, 102, 241, 0.6);
    box-shadow: inset 0 0 15px rgba(99, 102, 241, 0.3);
}

.front  { transform: translateZ(30px); }
.back   { transform: rotateY(180deg) translateZ(30px); }
.left   { transform: rotateY(-90deg) translateZ(30px); }
.right  { transform: rotateY(90deg) translateZ(30px); }
.top    { transform: rotateX(90deg) translateZ(30px); }
.bottom { transform: rotateX(-90deg) translateZ(30px); }

.scanner-line {
    position: absolute;
    top: 0;
    left: -20px;
    width: 140px;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--primary-500), transparent);
    box-shadow: 0 0 15px var(--primary-500);
    animation: scanLine 2s infinite ease-in-out;
}

.processing-title {
    font-size: 1.4em;
    font-weight: 600;
    color: var(--text-main);
    margin: 0;
    text-shadow: 0 0 10px rgba(99, 102, 241, 0.5);
}

.processing-status {
    font-size: 0.9em;
    opacity: 0.7;
    margin-top: 8px;
    letter-spacing: 1px;
    text-transform: uppercase;
}

@keyframes rotateCube {
    from { transform: rotateX(0deg) rotateY(0deg); }
    to { transform: rotateX(360deg) rotateY(360deg); }
}

@keyframes pulseCube {
    0%, 100% { scale: 1; }
    50% { scale: 1.15; }
}

@keyframes scanLine {
    100% { top: 110px; opacity: 0; }
}

/* Error State Styling */
.error-container {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: radial-gradient(circle at center, rgba(239, 68, 68, 0.1) 0%, transparent 70%);
    text-align: center;
    padding: 20px;
}

.error-icon svg {
    width: 64px;
    height: 64px;
    margin-bottom: 20px;
    color: #ef4444;
    filter: drop-shadow(0 0 10px rgba(239, 68, 68, 0.5));
}

.error-title {
    font-size: 1.5em;
    font-weight: 600;
    color: #ef4444;
    margin-bottom: 12px;
}

.error-message {
    font-size: 1em;
    color: var(--text-main);
    opacity: 0.8;
    max-width: 80%;
    line-height: 1.5;
    background: rgba(0,0,0,0.4);
    padding: 12px;
    border-radius: 6px;
    border: 1px solid rgba(239, 68, 68, 0.3);
}

.archeon-progress-fill.error {
    background: #ef4444 !important;
    box-shadow: 0 0 10px #ef4444;
}
"""

HTML_ERROR_TEMPLATE = """
<div class="error-container">
    <div class="error-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
    </div>
    <h3 class="error-title">Generation Failed</h3>
    <p class="error-message">#error_message#</p>
</div>
"""
