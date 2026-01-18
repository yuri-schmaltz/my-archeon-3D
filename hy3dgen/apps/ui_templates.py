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
    overflow: hidden !important; /* No scroll on container itself */
}

.right-col {
    height: 100% !important;
    padding: 16px !important;
    display: flex !important;
    flex-direction: column !important;
    overflow: hidden !important;
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
}

#gen_output_container > .form {
    height: 100% !important;
    flex: 1 !important;
    display: flex !important;
    flex-direction: column !important;
}

#model_3d_viewer {
    flex: 1 1 auto !important; /* Grow to fill available space */
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    min-height: 0 !important;
    position: relative !important; /* Anchor for absolute placeholder */
}

/* Ensure Iframe container (Gradio HTML) fills space recursively */
#model_3d_viewer,
#model_3d_viewer > .prose, 
#model_3d_viewer > .prose > div,
#model_3d_viewer > div,
#model_3d_viewer iframe {
    height: 100% !important;
    width: 100% !important;
    max-width: none !important;
    display: flex !important;
    flex-direction: column !important;
    overflow: hidden !important;
    border: none !important;
    margin: 0 !important;
    padding: 0 !important;
    flex-grow: 1 !important;
}

/* Scroll Area: Takes all available space */
.scroll-area {
    flex: 1 1 auto !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
    padding-right: 8px !important; /* Space for scrollbar */
    min-height: 0 !important; /* Firefox flex fix */
}

/* Footer Area: Doc at bottom */
.footer-area {
    flex: 0 0 auto !important;
    padding-top: 12px !important;
    border-top: 1px solid var(--surface-200) !important;
    background: var(--bg-app) !important;
    z-index: 50 !important;
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
.tabs {
    margin-bottom: 0 !important;
}
.tab-nav {
    border-bottom: 1px solid var(--surface-200) !important;
}
button.selected {
    border-bottom: 2px solid var(--primary-500) !important;
    color: var(--primary-500) !important;
    background: transparent !important;
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
    opacity: 0.3 !important;
    text-align: center !important;
    pointer-events: none !important; /* Let clicks pass through if needed */
}
.empty-placeholder-icon svg {
    width: 64px;
    height: 64px;
    margin-bottom: 16px;
}
.empty-placeholder-title {
    font-size: 1.5em;
    font-weight: 600;
    margin-bottom: 8px;
}

/* Custom Archeon Progress Bar */
.archeon-progress-container {
    width: 100%;
    margin-top: 8px; /* Space from viewer */
    margin-bottom: 8px; /* Space from footer */
    background: var(--surface-200);
    border-radius: 4px;
    height: 20px;
    position: relative;
    overflow: hidden;
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
"""
