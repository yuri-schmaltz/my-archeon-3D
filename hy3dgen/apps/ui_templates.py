
"""
Archeon 3D - UI Templates & Styles
Reconstructed based on system knowledge and previous patches.
"""

CSS_STYLES = """
/* Global Reset & Base */
body, gradio-app {
    background-color: #0b0f19 !important;
    color: #e2e8f0 !important;
    font-family: 'Inter', sans-serif !important;
}

header { display: none !important; }
footer { display: none !important; }

/* Main Containers */
.gradio-container {
    max-width: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
    background-color: #0b0f19 !important;
}

/* Layout Columns */
.column-input {
    background-color: #111827;
    border-right: 1px solid #1f2937;
    height: 100vh !important;
    overflow-y: auto;
    padding: 20px !important;
}

.column-viewer {
    background-color: #000000;
    height: 100vh !important;
    display: flex !important;
    align-items: center;
    justify-content: center;
    padding: 0 !important;
    overflow: hidden !important;
}

/* Prompt & Input Areas - Responsive Fix */
.prompt-container {
    height: auto !important; /* Fixed: Removed fixed 320px height */
    min-height: 250px !important;
    display: flex !important;
    flex-direction: column !important;
    gap: 10px;
}

/* Custom Components */
.custom-btn-primary {
    background: linear-gradient(90deg, #4f46e5 0%, #3b82f6 100%) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    transition: all 0.2s ease;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.custom-btn-primary:hover {
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    transform: translateY(-1px);
}

.custom-btn-stop {
    background: #ef4444 !important;
    color: white !important;
    border: none !important;
    font-weight: 600 !important;
}

/* Viewer Overlay */
.viewer-overlay {
    position: absolute;
    top: 20px;
    right: 20px;
    z-index: 100;
}

/* Progress Bar Overrides */
.progress-container {
    background: #1f2937 !important;
    border-radius: 4px;
}
.progress-bar {
    background: #3b82f6 !important;
}
"""

HTML_TEMPLATE_MODEL_VIEWER = """
<div style="width: 100%; height: 100%; display: flex; justify-content: center; align-items: center; background: radial-gradient(circle at center, #1f2937 0%, #000000 100%);">
    <model-viewer 
        src="{file_url}" 
        poster="{poster_url}" 
        shadow-intensity="1" 
        camera-controls 
        auto-rotate
        ar
        style="width: 100%; height: 100%; min-height: 600px;"
        background-color="#000000">
    </model-viewer>
</div>
"""

HTML_PLACEHOLDER = """
<div style="width: 100%; height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; color: #4b5563;">
    <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
        <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
        <line x1="12" y1="22.08" x2="12" y2="12"></line>
    </svg>
    <p style="margin-top: 1rem; font-size: 0.9rem;">Generated Mesh Preview</p>
</div>
"""

HTML_ERROR_TEMPLATE = """
<div style="width: 100%; height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center; color: #ef4444; background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 8px;">
    <h3 style="margin-bottom: 0.5rem;">Generation Failed</h3>
    <p style="font-size: 0.9rem; max-width: 80%; text-align: center;">#error_message#</p>
</div>
"""
