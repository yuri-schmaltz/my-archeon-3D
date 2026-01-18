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
            width: 100%; 
            height: 100%; 
            --progress-bar-color: var(--primary-500); 
            background: transparent;
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

def load_css():
    try:
        css_path = Path(__file__).parent / "assets" / "theme.css"
        if css_path.exists():
            return css_path.read_text(encoding="utf-8")
        return ""
    except Exception:
        return ""

CSS_STYLES = load_css()
